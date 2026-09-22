from __future__ import annotations

import argparse
import fcntl
import json
import os
import time
from pathlib import Path
from typing import Any

from companyos.runtime import adaptive_offload_calibration as calibration
from companyos.runtime import distributed_compute_scheduler as scheduler

RT=Path.home()/".companyos_runtime"
STATE=RT/"adaptive_offload_calibration_resumer_state.json"
LOCK=RT/"adaptive_offload_calibration_resumer.lock"
POLL=max(15,int(os.getenv("COMPANYOS_OFFLOAD_CALIBRATION_RESUME_SECONDS","60")))
REQUIRED_SLOTS=4


def load(path:Path,default:Any):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def atomic(path:Path,obj:Any)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    tmp.replace(path)
    try:path.chmod(0o600)
    except Exception:pass


def utc_day()->str:
    return time.strftime("%Y-%m-%d",time.gmtime())


def capacity_snapshot()->dict[str,Any]:
    used=int(scheduler.dispatched_today())
    cap=int(scheduler.DAILY_CAP)
    return {
        "utc_day":utc_day(),
        "dispatches_used":used,
        "daily_cap":cap,
        "dispatch_slots_available":max(0,cap-used),
        "required_calibration_slots":REQUIRED_SLOTS,
    }


def decide()->dict[str,Any]:
    existing=load(calibration.STATE,{})
    cap=capacity_snapshot()

    if existing.get("status")=="completed":
        return {
            "action":"sleep_completed",
            "reason":"calibration_already_completed",
            "calibration_status":"completed",
            **cap,
        }

    if int(cap["dispatch_slots_available"]) < REQUIRED_SLOTS:
        return {
            "action":"wait",
            "reason":"daily_dispatch_capacity",
            "calibration_status":existing.get("status") or "not_started",
            **cap,
        }

    if len(scheduler.active_jobs()) >= scheduler.MAX_INFLIGHT:
        return {
            "action":"wait",
            "reason":"inflight_capacity",
            "calibration_status":existing.get("status") or "not_started",
            **cap,
        }

    return {
        "action":"run_calibration",
        "reason":"capacity_available",
        "calibration_status":existing.get("status") or "not_started",
        **cap,
    }


def once(run_when_ready:bool=True)->dict[str,Any]:
    decision=decide()
    out={
        "schema":"companyos.adaptive_offload_calibration_resumer.v69_35d3",
        "healthy":True,
        "updated_at_unix":time.time(),
        **decision,
    }

    if decision["action"]=="run_calibration" and run_when_ready:
        atomic(STATE,{**out,"status":"starting_calibration"})
        report=calibration.run()
        out={
            **out,
            "status":"calibration_finished",
            "calibration_report_status":(
                "completed"
                if (report.get("summary") or {}).get("completed")==len(calibration.PLAN)
                else "incomplete"
            ),
            "report_path":str(calibration.REPORT),
            "updated_at_unix":time.time(),
        }
    elif decision["action"]=="wait":
        out["status"]="waiting_for_daily_cap_reset" if decision["reason"]=="daily_dispatch_capacity" else "waiting_for_capacity"
    else:
        out["status"]="completed"

    atomic(STATE,out)
    return out


def loop()->None:
    LOCK.parent.mkdir(parents=True,exist_ok=True)
    with LOCK.open("a+") as lock:
        try:
            fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            atomic(STATE,{
                "schema":"companyos.adaptive_offload_calibration_resumer.v69_35d3",
                "healthy":True,
                "status":"already_running",
                "updated_at_unix":time.time(),
            })
            return

        while True:
            try:
                out=once(run_when_ready=True)
                if out.get("status")=="calibration_finished":
                    time.sleep(max(POLL,300))
                else:
                    time.sleep(POLL)
            except Exception as exc:
                atomic(STATE,{
                    "schema":"companyos.adaptive_offload_calibration_resumer.v69_35d3",
                    "healthy":False,
                    "status":"error",
                    "error":f"{type(exc).__name__}:{str(exc)[:1000]}",
                    "updated_at_unix":time.time(),
                })
                time.sleep(POLL)


def status()->dict[str,Any]:
    return {
        "resumer":load(STATE,{"status":"not_started"}),
        "decision_now":decide(),
        "calibration":load(calibration.STATE,{"status":"not_started"}),
    }


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("once","loop","status"))
    a=p.parse_args()
    if a.command=="loop":
        loop()
        return 0
    if a.command=="once":
        print(json.dumps(once(),indent=2,sort_keys=True,default=str))
    else:
        print(json.dumps(status(),indent=2,sort_keys=True,default=str))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
