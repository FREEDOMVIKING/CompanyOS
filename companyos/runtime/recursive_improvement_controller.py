from __future__ import annotations
import json, os, time, traceback
from pathlib import Path

ROOT=(Path.home()/"companyos").resolve()
RT=ROOT/".companyos_runtime"
BASE=RT/"recursive_improvement"
STATE=BASE/"state.json"
EVENTS=BASE/"events.jsonl"
HISTORY=BASE/"history.json"
STOP=RT/"STOP_CONTINUOUS"

MAX_PROMOTIONS_PER_HOUR=max(1,int(os.getenv("COMPANYOS_RECURSIVE_MAX_PROMOTIONS_PER_HOUR","3")))
MAX_PROMOTIONS_PER_DAY=max(1,int(os.getenv("COMPANYOS_RECURSIVE_MAX_PROMOTIONS_PER_DAY","12")))
MAX_LINEAGE_DEPTH=max(1,int(os.getenv("COMPANYOS_RECURSIVE_MAX_LINEAGE_DEPTH","6")))
COOLDOWN_SECONDS=max(60,int(os.getenv("COMPANYOS_RECURSIVE_COOLDOWN_SECONDS","300")))

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

def feedback_state():
    return load(RT/"capability_feedback_state.json",{})

def queue_state():
    return load(RT/"capability_expansion/next_capability_queue.json",{"requests":[]})

def service_state():
    return load(RT/"service_supervisor_state.json",{})

def summary_snapshot():
    fb=feedback_state()
    caps=fb.get("capabilities",{}) if isinstance(fb,dict) else {}
    if isinstance(caps,list):
        caps={str(x.get("capability_id") or x.get("id") or i):x for i,x in enumerate(caps) if isinstance(x,dict)}
    return {
        "active":sum(1 for v in caps.values() if isinstance(v,dict) and v.get("status")=="active"),
        "probation":sum(1 for v in caps.values() if isinstance(v,dict) and v.get("status")=="probation"),
        "quarantined":sum(1 for v in caps.values() if isinstance(v,dict) and v.get("status")=="quarantined"),
        "failures":sum(int(v.get("failures",0) or 0) for v in caps.values() if isinstance(v,dict)),
        "capability_count":len(caps),
        "service_failures":sum(int(v.get("consecutive_failures",0) or 0) for v in (service_state().get("services") or {}).values() if isinstance(v,dict)),
    }

def _history():
    h=load(HISTORY,{"promotions":[],"seen_requests":{},"cycles":0})
    h.setdefault("promotions",[]);h.setdefault("seen_requests",{});h.setdefault("cycles",0)
    return h

def _prune_promotions(items,now):
    return [x for x in items if now-float(x.get("ts",0) or 0) <= 86400]

def promotion_limits_ok(h,now):
    h["promotions"]=_prune_promotions(h["promotions"],now)
    hour=sum(1 for x in h["promotions"] if now-float(x.get("ts",0) or 0)<=3600)
    day=len(h["promotions"])
    if hour>=MAX_PROMOTIONS_PER_HOUR:return False,"hourly_promotion_limit"
    if day>=MAX_PROMOTIONS_PER_DAY:return False,"daily_promotion_limit"
    return True,"ok"

def lineage_depth(req):
    depth=1
    source=req.get("source_capability")
    seen=set()
    q=queue_state().get("requests",[])
    by_req={x.get("requested_capability"):x for x in q if isinstance(x,dict)}
    while source and source not in seen:
        seen.add(source);depth+=1
        parent=by_req.get(source)
        if not parent:break
        source=parent.get("source_capability")
    return depth

def request_guard(req,h,now):
    if not isinstance(req,dict):return False,"request_not_dict"
    gid=str(req.get("gap_id") or "")
    cap=str(req.get("requested_capability") or "")
    if not cap:return False,"missing_requested_capability"
    if lineage_depth(req)>MAX_LINEAGE_DEPTH:return False,"lineage_depth_limit"
    prev=h["seen_requests"].get(gid or cap)
    if prev and now-float(prev.get("last_seen",0) or 0)<COOLDOWN_SECONDS:
        return False,"request_cooldown"
    # Reject circular names: exact source recurrence or repeated suffix explosions.
    src=str(req.get("source_capability") or "")
    if src and cap==src:return False,"self_cycle"
    if cap.count("_downstream_gap_detector")>2:return False,"recursive_name_cycle"
    return True,"ok"

def newest_pending_request():
    q=queue_state().get("requests",[])
    pending=[x for x in q if isinstance(x,dict) and x.get("status")=="research_required"]
    pending.sort(key=lambda r:(-int(r.get("profit_directed_priority",r.get("priority",0)) or 0),float(r.get("created_at",0) or 0),str(r.get("requested_capability",""))))
    return pending[0] if pending else None

def quarantine(capability_id,reason):
    fb=feedback_state()
    caps=fb.get("capabilities")
    if not isinstance(caps,dict) or capability_id not in caps:return False
    rec=caps[capability_id]
    if not isinstance(rec,dict):return False
    rec["status"]="quarantined"
    rec["quarantine_reason"]=reason
    rec["quarantined_at"]=time.time()
    atomic(RT/"capability_feedback_state.json",fb)
    emit("capability_quarantined",capability=capability_id,reason=reason)
    return True

def detect_regression(before,after,new_capability=None):
    reasons=[]
    if after["service_failures"]>before["service_failures"]:reasons.append("service_failures_increased")
    if after["quarantined"]>before["quarantined"]:reasons.append("quarantined_count_increased")
    if after["failures"]>before["failures"]+1:reasons.append("capability_failures_increased")
    if after["active"]<before["active"]:reasons.append("active_capabilities_decreased")
    if reasons and new_capability:
        quarantine(new_capability,";".join(reasons))
    return reasons

def one_cycle():
    from companyos.runtime import capability_feedback as feedback
    from companyos.runtime import compounding_capability_expansion as compound
    from companyos.runtime import semantic_capability_bridge as semantic
    from companyos.runtime import profit_directed_capability_priority as profit_priority
    from companyos.runtime import capability_request_executor as executor

    now=time.time()
    h=_history()
    before=summary_snapshot()

    # COMPANYOS_RECURSIVE_SEMANTIC_LOOP_V14
    # Refresh observations first.
    feedback_result=feedback.cycle()

    # Two complementary gap sources: usage/feedback and semantic capability output.
    compound_result=compound.once()
    semantic_before=semantic.cycle()

    # COMPANYOS_PROFIT_DIRECTED_RECURSION_V16
    profit_priority_before=profit_priority.cycle()

    # Prefer the highest-ranked guarded request now pending.
    req=newest_pending_request()

    selected=None
    executor_result={"status":"idle","reason":"no_pending_request"}
    if req:
        ok,reason=request_guard(req,h,now)
        key=str(req.get("gap_id") or req.get("requested_capability"))
        h["seen_requests"][key]={"last_seen":now,"reason":reason}
        if ok:
            limits_ok,limit_reason=promotion_limits_ok(h,now)
            if limits_ok:
                selected=req.get("requested_capability")
                executor_state=executor.cycle()
                executor_result=executor_state.get("result",executor_state)
                if executor_result.get("status")=="capability_promoted_and_used":
                    h["promotions"].append({"ts":time.time(),"capability":executor_result.get("capability"),"candidate_id":executor_result.get("candidate_id")})
            else:
                executor_result={"status":"blocked","reason":limit_reason}
        else:
            executor_result={"status":"blocked","reason":reason}

    # Observe the resulting system and catch regressions.
    feedback_after=feedback.cycle()

    # Inspect the just-completed capability output immediately and enqueue at most
    # one next semantic request. It is not executed until a later controller cycle.
    semantic_after=semantic.cycle()

    after=summary_snapshot()
    promoted=executor_result.get("capability") if isinstance(executor_result,dict) and executor_result.get("status")=="capability_promoted_and_used" else None
    regression=detect_regression(before,after,promoted)

    h["cycles"]=int(h.get("cycles",0))+1
    h["last_cycle_unix"]=time.time()
    atomic(HISTORY,h)

    result={
        "healthy":not regression,
        "before":before,
        "after":after,
        "selected_request":selected,
        "feedback_before":feedback_result.get("summary") if isinstance(feedback_result,dict) else None,
        "compound":compound_result,
        "semantic_before":semantic_before,
        "profit_priority_before":profit_priority_before,
        "executor":executor_result,
        "feedback_after":feedback_after.get("summary") if isinstance(feedback_after,dict) else None,
        "semantic_after":semantic_after,
        "regression_reasons":regression,
        "limits":{
            "max_promotions_per_hour":MAX_PROMOTIONS_PER_HOUR,
            "max_promotions_per_day":MAX_PROMOTIONS_PER_DAY,
            "max_lineage_depth":MAX_LINEAGE_DEPTH,
            "cooldown_seconds":COOLDOWN_SECONDS,
        },
    }
    state={"running":True,"last_cycle_unix":time.time(),"result":result}
    atomic(STATE,state)
    emit("recursive_cycle",selected_request=selected,executor_status=executor_result.get("status"),regression=regression)
    return state

def run():
    interval=max(180,int(os.getenv("COMPANYOS_RECURSIVE_IMPROVEMENT_INTERVAL_SECONDS","600")))
    while not STOP.exists():
        try:one_cycle()
        except Exception as exc:
            atomic(STATE,{"running":True,"last_cycle_unix":time.time(),"result":{"healthy":False,"status":"cycle_exception","error":repr(exc)}})
            emit("cycle_exception",error=repr(exc),traceback=traceback.format_exc()[-4000:])
        time.sleep(interval)

if __name__=="__main__":
    import argparse
    a=argparse.ArgumentParser();a.add_argument("command",nargs="?",default="run",choices=("run","once","status","history"));cmd=a.parse_args().command
    if cmd=="run":run()
    elif cmd=="once":print(json.dumps(one_cycle(),indent=2,sort_keys=True,default=str))
    elif cmd=="history":print(json.dumps(_history(),indent=2,sort_keys=True,default=str))
    else:print(json.dumps(load(STATE,{"status":"not_run"}),indent=2,sort_keys=True,default=str))
