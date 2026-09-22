from __future__ import annotations

import argparse
import json
import time
import uuid
from pathlib import Path
from typing import Any

from companyos.runtime import adaptive_offload_controller as offload
from companyos.runtime import distributed_compute_scheduler as scheduler
from companyos.runtime import github_actions_worker_pool as pool

RT=Path.home()/".companyos_runtime"
STATE=RT/"adaptive_offload_calibration_state.json"
REPORT=RT/"adaptive_offload_calibration_report.json"
LOG=RT/"adaptive_offload_calibration_events.jsonl"
PLAN=(1,2,4,8)


def atomic(path:Path,obj:Any)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    tmp.replace(path)
    try:path.chmod(0o600)
    except Exception:pass


def emit(kind:str,**data:Any)->None:
    LOG.parent.mkdir(parents=True,exist_ok=True)
    with LOG.open("a",encoding="utf-8") as f:
        f.write(json.dumps({"ts":time.time(),"kind":kind,**data},sort_keys=True,default=str)+"\n")


def find_job(job_id:str)->dict[str,Any]|None:
    for row in pool.queue_state().get("jobs") or []:
        if isinstance(row,dict) and row.get("job_id")==job_id:
            return row
    return None


def duration_seconds(job:dict[str,Any])->float|None:
    start=float(job.get("dispatched_at_unix") or job.get("created_at_unix") or 0)
    end=float(job.get("completed_at_unix") or job.get("updated_at_unix") or 0)
    if start<=0 or end<start:
        return None
    return round(end-start,2)


def summarize(rows:list[dict[str,Any]])->dict[str,Any]:
    completed=[r for r in rows if r.get("status")=="completed"]
    durations=[float(r["duration_seconds"]) for r in completed if isinstance(r.get("duration_seconds"),(int,float))]
    by_shards={}
    for r in rows:
        by_shards[str(r.get("requested_shards"))]={
            "status":r.get("status"),
            "run_id":r.get("run_id"),
            "duration_seconds":r.get("duration_seconds"),
            "shard_results":r.get("shard_results"),
            "phone_pressure_before":r.get("phone_pressure_before"),
            "phone_pressure_after":r.get("phone_pressure_after"),
        }
    return {
        "runs":len(rows),
        "completed":len(completed),
        "failed":sum(1 for r in rows if r.get("status")!="completed"),
        "success_rate":round(len(completed)/len(rows),4) if rows else 0.0,
        "average_turnaround_seconds":round(sum(durations)/len(durations),2) if durations else None,
        "best_turnaround_seconds":min(durations) if durations else None,
        "worst_turnaround_seconds":max(durations) if durations else None,
        "by_shards":by_shards,
    }


def wait_for_capacity(timeout_seconds:int=1800)->tuple[bool,str]:
    deadline=time.time()+timeout_seconds
    while time.time()<deadline:
        allowed,reason=scheduler.can_enqueue(ignore_calibration_lock=True)
        if allowed:
            return True,"ready"
        if reason=="daily_cap":
            return False,"daily_cap"
        time.sleep(5)
    return False,"capacity_wait_timeout"


def wait_for_terminal(job_id:str,timeout_seconds:int=1800)->dict[str,Any]:
    deadline=time.time()+timeout_seconds
    while time.time()<deadline:
        row=find_job(job_id)
        if row and row.get("status") in {"completed","failed","blocked"}:
            return row
        time.sleep(10)
    row=find_job(job_id) or {"job_id":job_id}
    row=dict(row)
    row["status"]="timeout"
    return row


def run()->dict[str,Any]:
    session="cal_"+uuid.uuid4().hex[:12]
    initial_dispatches=scheduler.dispatched_today()
    if initial_dispatches+len(PLAN)>scheduler.DAILY_CAP:
        out={
            "schema":"companyos.adaptive_offload_calibration.v69_35d2",
            "healthy":False,
            "status":"blocked_daily_cap",
            "initial_dispatches":initial_dispatches,
            "daily_cap":scheduler.DAILY_CAP,
            "required_slots":len(PLAN),
            "updated_at_unix":time.time(),
        }
        atomic(STATE,out)
        return out

    state={
        "schema":"companyos.adaptive_offload_calibration.v69_35d2",
        "healthy":True,
        "status":"running",
        "session":session,
        "plan":list(PLAN),
        "started_at_unix":time.time(),
        "results":[],
    }
    atomic(STATE,state)
    emit("calibration_started",session=session,plan=list(PLAN))

    results=[]
    for shards in PLAN:
        ok,reason=wait_for_capacity()
        if not ok:
            results.append({"requested_shards":shards,"status":"not_dispatched","reason":reason})
            break

        phone_before=offload.phone_metrics()
        payload={
            "calibration":"v69_35d2",
            "session":session,
            "requested_shards":shards,
            "message":"CompanyOS adaptive offload capacity calibration",
        }
        job=pool.enqueue(
            "smoke",
            payload,
            shards=shards,
            dedupe_key=f"adaptive_calibration:{session}:{shards}",
        )
        scheduler.record_dispatch(job,"adaptive_offload_calibration")
        emit("calibration_dispatched",job_id=job.get("job_id"),requested_shards=shards)

        final=wait_for_terminal(str(job["job_id"]))
        phone_after=offload.phone_metrics()
        row={
            "job_id":final.get("job_id"),
            "run_id":final.get("run_id"),
            "requested_shards":shards,
            "status":final.get("status"),
            "github_conclusion":final.get("github_conclusion"),
            "shard_results":int(final.get("shard_results") or 0),
            "duration_seconds":duration_seconds(final),
            "phone_pressure_before":phone_before.get("phone_pressure_score"),
            "phone_pressure_after":phone_after.get("phone_pressure_score"),
        }
        results.append(row)
        state["results"]=results
        state["updated_at_unix"]=time.time()
        atomic(STATE,state)
        emit("calibration_completed",**row)

        if final.get("status")!="completed":
            break

    summary=summarize(results)
    current_queue=pool.queue_state()
    worker=offload.worker_metrics(current_queue)
    recommendation=offload.decide(
        kind="research",
        work_items=12,
        queue=current_queue,
        max_shards=scheduler.MAX_SHARDS,
    )

    report={
        "schema":"companyos.adaptive_offload_calibration_report.v69_35d2",
        "session":session,
        "generated_at_unix":time.time(),
        "plan":list(PLAN),
        "summary":summary,
        "post_calibration_worker_metrics":worker,
        "post_calibration_recommendation":recommendation,
        "dispatches_today":scheduler.dispatched_today(),
        "daily_dispatch_cap":scheduler.DAILY_CAP,
        "financial_actions_performed":False,
        "deployments_performed":False,
        "account_creation_performed":False,
        "external_messages_sent":False,
    }
    atomic(REPORT,report)

    state.update({
        "status":"completed" if summary["completed"]==len(PLAN) else "incomplete",
        "healthy":summary["completed"]==len(PLAN),
        "finished_at_unix":time.time(),
        "summary":summary,
        "report_path":str(REPORT),
        "updated_at_unix":time.time(),
    })
    atomic(STATE,state)
    emit("calibration_finished",status=state["status"],summary=summary)
    return report


def status()->dict[str,Any]:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {"status":"not_started","state_path":str(STATE)}


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("run","status","report"))
    a=p.parse_args()
    if a.command=="run":
        out=run()
    elif a.command=="status":
        out=status()
    else:
        try:
            out=json.loads(REPORT.read_text(encoding="utf-8"))
        except Exception:
            out={"status":"no_report","report_path":str(REPORT)}
    print(json.dumps(out,indent=2,sort_keys=True,default=str))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
