from __future__ import annotations
import json, os, time, hashlib
from pathlib import Path

ROOT=Path.home()/"companyos"
RT=ROOT/".companyos_runtime"
ACTION_QUEUE=RT/"profit_execution_action_queue.json"
STATE=RT/"closed_loop_outcome_evaluator_state.json"
EVENTS=RT/"closed_loop_outcome_evaluator_events.jsonl"
FEEDBACK=RT/"capability_feedback_state.json"
STOP=RT/"STOP_CONTINUOUS"

CANDIDATE_DIR=RT/"profit_first_candidates"

def load(path,default=None):
    if default is None: default={}
    try:return json.loads(Path(path).read_text(encoding="utf-8"))
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

def numeric(v,default=0.0):
    try:return float(v)
    except Exception:return default

def _find_candidate(name):
    if not CANDIDATE_DIR.exists():return None,None
    for p in CANDIDATE_DIR.glob("*.json"):
        x=load(p,None)
        if not isinstance(x,dict):continue
        n=str(x.get("name") or x.get("candidate_name") or x.get("venture_name") or p.stem)
        if n==name:return p,x
    return None,None

def _extract_metrics(payload):
    if not isinstance(payload,dict):payload={}
    scores=payload.get("scores") if isinstance(payload.get("scores"),dict) else {}
    def first(keys,default=0.0):
        for k in keys:
            if k in payload:return numeric(payload.get(k),default)
            if k in scores:return numeric(scores.get(k),default)
        return default
    return {
        "profit": first(("expected_profit","profit","profit_score","profitability_score"),0.0),
        "probability": first(("probability","success_probability","confidence","confidence_score"),0.0),
        "readiness": first(("readiness","readiness_score","execution_readiness"),0.0),
        "score": first(("score","total_score","composite_score","opportunity_score"),0.0),
        "evidence_count": len(payload.get("evidence",[])) if isinstance(payload.get("evidence"),list) else 0,
    }

def _packet_key(packet):
    return str(packet.get("action_packet_id") or hashlib.sha256(json.dumps(packet,sort_keys=True,default=str).encode()).hexdigest()[:20])

def _action_outcome(packet):
    outcome=packet.get("outcome")
    if isinstance(outcome,dict):return outcome
    result=packet.get("result")
    if isinstance(result,dict):return result
    return {}

def _score_outcome(before,after,outcome):
    delta_profit=after["profit"]-before["profit"]
    delta_prob=after["probability"]-before["probability"]
    delta_ready=after["readiness"]-before["readiness"]
    delta_score=after["score"]-before["score"]
    delta_evidence=after["evidence_count"]-before["evidence_count"]

    explicit=numeric(outcome.get("utility_score"),0.0)
    success=bool(outcome.get("success") or outcome.get("validated") or outcome.get("completed"))
    failure=bool(outcome.get("failed") or outcome.get("error"))

    utility=0.0
    utility += max(-25,min(25,delta_profit*0.25))
    utility += max(-20,min(20,delta_prob*0.20))
    utility += max(-20,min(20,delta_ready*0.20))
    utility += max(-20,min(20,delta_score*0.20))
    utility += max(-10,min(10,delta_evidence*2))
    utility += max(-10,min(10,explicit*10))
    if success: utility+=10
    if failure: utility-=20
    return round(max(-100,min(100,utility)),2)

def _update_capability_feedback(capability_ids,utility):
    fb=load(FEEDBACK,{})
    caps=fb.get("capabilities")
    if not isinstance(caps,dict):return False
    changed=False
    for cid in capability_ids:
        rec=caps.get(cid)
        if not isinstance(rec,dict):continue
        prior=numeric(rec.get("utility_score"),0.5)
        observed=int(rec.get("uses_observed",0) or 0)
        # bounded moving average
        normalized=max(0.0,min(1.0,(utility+100)/200))
        rec["utility_score"]=round((prior*max(1,observed)+normalized)/(max(1,observed)+1),4)
        rec["uses_observed"]=observed+1
        rec["last_outcome_utility"]=utility
        rec["last_outcome_at"]=time.time()
        if utility <= -25:
            rec["failures"]=int(rec.get("failures",0) or 0)+1
        else:
            rec["successes"]=int(rec.get("successes",0) or 0)+1
        changed=True
    if changed:atomic(FEEDBACK,fb)
    return changed

def cycle():
    q=load(ACTION_QUEUE,{"actions":[]})
    actions=q.get("actions")
    if not isinstance(actions,list):actions=[]

    processed_state=load(STATE,{"processed":{},"cycles":0})
    processed=processed_state.setdefault("processed",{})

    evaluated=[]
    for packet in actions:
        if not isinstance(packet,dict):continue
        key=_packet_key(packet)
        if key in processed:continue

        status=str(packet.get("status") or "")
        outcome=_action_outcome(packet)
        # Only score actual outcomes, not merely queued plans.
        if status not in ("completed","evaluated","outcome_recorded") and not outcome:
            continue

        name=str(packet.get("candidate_name") or "")
        path,payload=_find_candidate(name)
        before=packet.get("candidate_metrics_before")
        if not isinstance(before,dict):
            before=_extract_metrics(packet.get("candidate_snapshot") or {})
        after=_extract_metrics(payload or {})

        utility=_score_outcome(before,after,outcome)

        capability_ids=[]
        for row in packet.get("capability_results",[]) or []:
            if isinstance(row,dict) and row.get("capability_id"):
                capability_ids.append(str(row["capability_id"]))
        _update_capability_feedback(capability_ids,utility)

        record={
            "action_packet_id":key,
            "candidate_name":name,
            "utility":utility,
            "before":before,
            "after":after,
            "outcome":outcome,
            "capabilities":capability_ids,
            "evaluated_at":time.time(),
        }
        processed[key]=record
        evaluated.append(record)
        emit("outcome_evaluated",**record)

    processed_state["cycles"]=int(processed_state.get("cycles",0))+1
    processed_state["last_cycle_unix"]=time.time()
    processed_state["evaluated_count"]=len(evaluated)
    processed_state["last_evaluated"]=evaluated[-10:]
    atomic(STATE,processed_state)

    return {
        "healthy":True,
        "evaluated_count":len(evaluated),
        "processed_total":len(processed),
        "last_evaluated":evaluated[-10:],
    }

def run():
    interval=max(120,int(os.getenv("COMPANYOS_OUTCOME_EVALUATOR_INTERVAL_SECONDS","300")))
    while not STOP.exists():
        try:cycle()
        except Exception as exc:
            emit("cycle_error",error=repr(exc))
        time.sleep(interval)

if __name__=="__main__":
    import argparse
    a=argparse.ArgumentParser()
    a.add_argument("command",nargs="?",default="run",choices=("run","once","status"))
    cmd=a.parse_args().command
    if cmd=="run":run()
    elif cmd=="once":print(json.dumps(cycle(),indent=2,sort_keys=True,default=str))
    else:print(json.dumps(load(STATE,{"status":"not_run"}),indent=2,sort_keys=True,default=str))
