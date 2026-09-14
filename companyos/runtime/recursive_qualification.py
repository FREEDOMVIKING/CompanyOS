from __future__ import annotations
import json, os, time, traceback
from pathlib import Path

ROOT=(Path.home()/"companyos").resolve()
RT=ROOT/".companyos_runtime"
BASE=RT/"recursive_qualification"
STATE=BASE/"state.json"
EVENTS=BASE/"events.jsonl"
REPORT=BASE/"latest_report.json"
STOP=RT/"STOP_CONTINUOUS"

DEFAULT_CYCLES=max(2,int(os.getenv("COMPANYOS_RECURSIVE_QUALIFICATION_CYCLES","4")))
DEFAULT_DELAY=max(10,int(os.getenv("COMPANYOS_RECURSIVE_QUALIFICATION_DELAY_SECONDS","20")))

def load(path,default=None):
    if default is None: default={}
    try:return json.loads(path.read_text(encoding="utf-8"))
    except Exception:return default

def atomic(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    tmp.replace(path)

def emit(kind,**kw):
    EVENTS.parent.mkdir(parents=True,exist_ok=True)
    with EVENTS.open("a",encoding="utf-8") as f:
        f.write(json.dumps({"ts":time.time(),"kind":kind,**kw},sort_keys=True,default=str)+"\n")

def inventory():
    try:
        from companyos.runtime import capability_expansion as ce
        return sorted(ce.capability_inventory())
    except Exception:
        return []

def feedback_summary():
    f=load(RT/"capability_feedback_state.json",{})
    return f.get("summary",{}) if isinstance(f,dict) else {}

def service_snapshot():
    s=load(RT/"service_supervisor_state.json",{})
    services=s.get("services",{}) if isinstance(s,dict) else {}
    return {
        name:{
            "running":bool(v.get("running")),
            "process_alive":bool(v.get("process_alive")),
            "consecutive_failures":int(v.get("consecutive_failures",0) or 0),
        }
        for name,v in services.items() if isinstance(v,dict)
    }

def queue_snapshot():
    q=load(RT/"capability_expansion/next_capability_queue.json",{"requests":[]})
    reqs=q.get("requests",[]) if isinstance(q,dict) else []
    if not isinstance(reqs,list): reqs=[]
    return {
        "total":len(reqs),
        "research_required":sum(1 for r in reqs if isinstance(r,dict) and r.get("status")=="research_required"),
        "generating":sum(1 for r in reqs if isinstance(r,dict) and r.get("status")=="generating"),
        "completed":sum(1 for r in reqs if isinstance(r,dict) and r.get("status")=="completed"),
        "rejected":sum(1 for r in reqs if isinstance(r,dict) and r.get("status")=="rejected"),
        "latest":[r for r in reqs[-5:] if isinstance(r,dict)],
    }

def bad_services(before,after):
    issues=[]
    for name,cur in after.items():
        if cur.get("consecutive_failures",0)>0:
            issues.append(f"{name}:consecutive_failures={cur['consecutive_failures']}")
        if name in before and before[name].get("running") and not cur.get("running"):
            issues.append(f"{name}:stopped")
    return issues

def duplicate_count():
    f=load(RT/"capability_feedback_state.json",{})
    if not isinstance(f,dict): return 0
    s=f.get("summary",{})
    if isinstance(s,dict): return int(s.get("duplicates",0) or 0)
    d=f.get("duplicates",[])
    return len(d) if isinstance(d,list) else 0

def quarantined_count():
    f=load(RT/"capability_feedback_state.json",{})
    if not isinstance(f,dict): return 0
    s=f.get("summary",{})
    if isinstance(s,dict): return int(s.get("quarantined",0) or 0)
    return 0

def run_qualification(cycles=DEFAULT_CYCLES,delay=DEFAULT_DELAY):
    from companyos.runtime import recursive_improvement_controller as ric
    from companyos.runtime import capability_feedback as feedback

    start_inv=inventory()
    start_services=service_snapshot()
    start_dups=duplicate_count()
    start_quarantine=quarantined_count()
    start_queue=queue_snapshot()

    runs=[]
    no_progress=0
    last_inv=list(start_inv)
    stop_reason=None

    for n in range(1,cycles+1):
        if STOP.exists():
            stop_reason="global_stop_requested"
            break

        before_inv=inventory()
        before_services=service_snapshot()
        before_queue=queue_snapshot()
        before_feedback=feedback_summary()

        try:
            state=ric.one_cycle()
            result=state.get("result",{}) if isinstance(state,dict) else {}
        except Exception as exc:
            result={"healthy":False,"status":"controller_exception","error":repr(exc)}
            stop_reason="controller_exception"
            emit("qualification_exception",cycle=n,error=repr(exc),traceback=traceback.format_exc()[-4000:])
            runs.append({"cycle":n,"result":result})
            break

        # one extra feedback pass ensures newly promoted capability is observed
        try:
            feedback.cycle()
        except Exception:
            pass

        after_inv=inventory()
        after_services=service_snapshot()
        after_queue=queue_snapshot()
        after_feedback=feedback_summary()

        new_caps=[x for x in after_inv if x not in before_inv]
        service_issues=bad_services(before_services,after_services)
        dups=duplicate_count()
        quarantined=quarantined_count()

        executor=(result.get("executor") or {}) if isinstance(result,dict) else {}
        executor_status=executor.get("status")
        regression=result.get("regression_reasons") or []

        progress=bool(new_caps) or after_queue["completed"]>before_queue["completed"] or after_queue["research_required"]!=before_queue["research_required"]
        if progress:
            no_progress=0
        else:
            no_progress+=1

        cycle_report={
            "cycle":n,
            "before_inventory":before_inv,
            "after_inventory":after_inv,
            "new_capabilities":new_caps,
            "before_queue":before_queue,
            "after_queue":after_queue,
            "executor_status":executor_status,
            "regression_reasons":regression,
            "service_issues":service_issues,
            "duplicates":dups,
            "quarantined":quarantined,
            "before_feedback":before_feedback,
            "after_feedback":after_feedback,
            "progress":progress,
        }
        runs.append(cycle_report)
        emit("qualification_cycle",**cycle_report)

        if service_issues:
            stop_reason="service_failure"
            break
        if regression:
            stop_reason="regression_detected"
            break
        if dups>start_dups:
            stop_reason="duplicate_growth"
            break
        if quarantined>start_quarantine:
            stop_reason="quarantine_growth"
            break
        if executor_status in ("validation_rejected","tests_rejected","canary_failed_rolled_back","generation_shape_invalid"):
            stop_reason="promotion_gate_failure"
            break
        if no_progress>=2:
            stop_reason="no_progress_two_cycles"
            break

        last_inv=after_inv
        if n<cycles:
            time.sleep(delay)

    end_inv=inventory()
    end_services=service_snapshot()
    end_queue=queue_snapshot()
    added=[x for x in end_inv if x not in start_inv]

    verdict="PASS"
    if stop_reason not in (None,"global_stop_requested"):
        verdict="FAIL"
    elif not added:
        verdict="PASS_NO_NEW_CAPABILITY"

    report={
        "verdict":verdict,
        "stop_reason":stop_reason,
        "requested_cycles":cycles,
        "completed_cycles":len(runs),
        "started_at":time.time() - sum(1 for _ in runs)*0,
        "finished_at":time.time(),
        "start_inventory":start_inv,
        "end_inventory":end_inv,
        "new_capabilities":added,
        "start_queue":start_queue,
        "end_queue":end_queue,
        "start_services":start_services,
        "end_services":end_services,
        "runs":runs,
    }
    atomic(REPORT,report)
    atomic(STATE,{"running":False,"last_run_unix":time.time(),"report":report})
    emit("qualification_complete",verdict=verdict,stop_reason=stop_reason,new_capabilities=added)
    return report

if __name__=="__main__":
    import argparse
    a=argparse.ArgumentParser()
    a.add_argument("command",nargs="?",default="run",choices=("run","status","report"))
    a.add_argument("--cycles",type=int,default=DEFAULT_CYCLES)
    a.add_argument("--delay",type=int,default=DEFAULT_DELAY)
    args=a.parse_args()

    if args.command=="run":
        print(json.dumps(run_qualification(max(1,args.cycles),max(0,args.delay)),indent=2,sort_keys=True,default=str))
    elif args.command=="report":
        print(json.dumps(load(REPORT,{"status":"not_run"}),indent=2,sort_keys=True,default=str))
    else:
        print(json.dumps(load(STATE,{"status":"not_run"}),indent=2,sort_keys=True,default=str))
