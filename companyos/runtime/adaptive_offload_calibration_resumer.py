from __future__ import annotations
import argparse, json, os, time
from pathlib import Path
from typing import Any
from companyos.runtime import adaptive_offload_calibration as calibration
from companyos.runtime import distributed_compute_scheduler as scheduler
from companyos.runtime import github_actions_worker_pool as pool

RT=Path.home()/".companyos_runtime"
STATE=RT/"adaptive_offload_calibration_resumer_state.json"
LOCK=RT/"adaptive_offload_calibration.lock"
INTERVAL=max(30,int(os.getenv("COMPANYOS_OFFLOAD_CALIBRATION_RESUMER_SECONDS","60")))

def atomic(path:Path,obj:Any)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    tmp.replace(path)
    try:path.chmod(0o600)
    except Exception:pass

def seconds_until_utc_reset(now:float|None=None)->int:
    ts=time.time() if now is None else float(now)
    next_day=((int(ts)//86400)+1)*86400
    return max(0,int(next_day-ts))

def required_slots(cal_state:dict[str,Any])->int:
    results=cal_state.get("results") if isinstance(cal_state.get("results"),list) else []
    completed_shards={int(r.get("requested_shards")) for r in results
        if isinstance(r,dict) and r.get("status")=="completed"
        and r.get("requested_shards") in calibration.PLAN}
    return max(0,len([x for x in calibration.PLAN if x not in completed_shards]))

def resume_eligible_status(status:str)->bool:
    return status in {"blocked_daily_cap","pending_daily_cap","waiting_daily_cap","not_started"}

def acquire_lock()->bool:
    try:
        LOCK.parent.mkdir(parents=True,exist_ok=True)
        fd=os.open(str(LOCK),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            f.write(json.dumps({"owner":"adaptive_offload_calibration_resumer","created_at_unix":time.time(),"pid":os.getpid()})+"\n")
        return True
    except FileExistsError:
        return False

def release_lock()->None:
    try: LOCK.unlink(missing_ok=True)
    except Exception: pass

def once()->dict[str,Any]:
    cal=calibration.status()
    cal_status=str(cal.get("status") or "not_started")
    used=scheduler.dispatched_today()
    remaining=max(0,scheduler.DAILY_CAP-used)
    needed=required_slots(cal)
    auth=pool.gh_ready()
    active=len(scheduler.active_jobs())

    out={
        "schema":"companyos.adaptive_offload_calibration_resumer.v69_35d3",
        "healthy":True,
        "updated_at_unix":time.time(),
        "calibration_status":cal_status,
        "dispatches_today":used,
        "daily_dispatch_cap":scheduler.DAILY_CAP,
        "remaining_dispatch_slots":remaining,
        "required_calibration_slots":needed,
        "active_jobs":active,
        "gh_ready":bool(auth.get("ready")),
        "seconds_until_utc_dispatch_reset":seconds_until_utc_reset(),
        "cap_bypassed":False,
        "cap_raised":False,
        "benchmark_lock_present":LOCK.exists(),
    }

    if cal_status=="completed":
        out.update(status="completed",decision="nothing_to_do")
        atomic(STATE,out); release_lock(); return out
    if cal_status=="running":
        out.update(status="calibration_running",decision="wait")
        atomic(STATE,out); return out
    if not resume_eligible_status(cal_status):
        out.update(status="manual_review",decision="do_not_auto_retry_non_cap_failure")
        atomic(STATE,out); return out
    if needed<=0:
        out.update(status="completed",decision="nothing_to_do")
        atomic(STATE,out); release_lock(); return out
    if remaining<needed:
        out.update(status="waiting_daily_cap",decision="wait_for_utc_cap_reset")
        atomic(STATE,out); return out
    if active>0:
        out.update(status="waiting_for_idle",decision="wait_for_clean_benchmark_window")
        atomic(STATE,out); return out
    if not auth.get("ready"):
        out.update(status="waiting_github",decision="wait_for_github_auth")
        atomic(STATE,out); return out
    if not acquire_lock():
        out.update(status="waiting_for_lock",decision="another_calibration_window_active")
        atomic(STATE,out); return out

    try:
        time.sleep(2)
        active_after=len(scheduler.active_jobs())
        used_after=scheduler.dispatched_today()
        remaining_after=max(0,scheduler.DAILY_CAP-used_after)
        if active_after>0 or remaining_after<needed:
            out.update(updated_at_unix=time.time(),status="waiting_for_clean_window",
                       decision="reservation_recheck_failed",active_jobs=active_after,
                       remaining_dispatch_slots=remaining_after,benchmark_lock_present=True)
            atomic(STATE,out); return out

        out.update(updated_at_unix=time.time(),status="launching",
                   decision="run_calibration",benchmark_lock_present=True)
        atomic(STATE,out)
        report=calibration.run()
        final_status=str((calibration.status() or {}).get("status") or "unknown")
        out.update(updated_at_unix=time.time(),
                   status="completed" if final_status=="completed" else "calibration_finished",
                   calibration_status=final_status,decision="calibration_finished",
                   report_summary=report.get("summary") if isinstance(report,dict) else None,
                   benchmark_lock_present=False)
        atomic(STATE,out)
        return out
    finally:
        release_lock()

def loop()->None:
    while True:
        try: once()
        except Exception as exc:
            release_lock()
            atomic(STATE,{"schema":"companyos.adaptive_offload_calibration_resumer.v69_35d3",
                          "healthy":False,"updated_at_unix":time.time(),"status":"error",
                          "error":f"{type(exc).__name__}:{str(exc)[:1000]}",
                          "cap_bypassed":False,"cap_raised":False})
        time.sleep(INTERVAL)

def status()->dict[str,Any]:
    try:return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:return {"status":"not_run","state_path":str(STATE)}

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("once","loop","status"))
    a=p.parse_args()
    if a.command=="once": out=once()
    elif a.command=="status": out=status()
    else: loop(); return 0
    print(json.dumps(out,indent=2,sort_keys=True,default=str))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
