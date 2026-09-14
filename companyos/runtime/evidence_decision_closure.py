from __future__ import annotations
import json, os, time, hashlib
from pathlib import Path

ROOT=Path.home()/"companyos"
RT=ROOT/".companyos_runtime"
STATE=RT/"evidence_decision_closure_state.json"
HISTORY=RT/"evidence_decision_history.jsonl"
STOP=RT/"STOP_CONTINUOUS"

EVIDENCE_QUEUE=RT/"evidence_acquisition_queue.json"
ACTION_QUEUE=RT/"profit_execution_action_queue.json"
CANDIDATE_DIR=RT/"profit_first_candidates"

READINESS_THRESHOLD=float(os.getenv("COMPANYOS_DECISION_READINESS_THRESHOLD","60"))
MIN_EVIDENCE_COVERAGE=float(os.getenv("COMPANYOS_MIN_EVIDENCE_COVERAGE","0.80"))

def load(path,default=None):
    if default is None: default={}
    try:return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:return default

def atomic(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    tmp.replace(path)

def append_history(obj):
    HISTORY.parent.mkdir(parents=True,exist_ok=True)
    with HISTORY.open("a",encoding="utf-8") as f:
        f.write(json.dumps(obj,sort_keys=True,default=str)+"\n")

def num(v,default=0.0):
    try:return float(v)
    except Exception:return default

def candidate_name(payload,path):
    return str(payload.get("name") or payload.get("candidate_name") or payload.get("venture_name") or path.stem)

def find_candidate(name):
    if not CANDIDATE_DIR.exists():return None,None
    for p in CANDIDATE_DIR.glob("*.json"):
        x=load(p,None)
        if isinstance(x,dict) and candidate_name(x,p)==name:
            return p,x
    return None,None

def latest_packet():
    q=load(ACTION_QUEUE,{"actions":[]})
    rows=q.get("actions",[]) if isinstance(q,dict) else []
    rows=[r for r in rows if isinstance(r,dict)]
    return (q,rows[-1]) if rows else (q,None)

def evidence_for(candidate):
    q=load(EVIDENCE_QUEUE,{"tasks":[]})
    tasks=q.get("tasks",[]) if isinstance(q,dict) else []
    rows=[t for t in tasks if isinstance(t,dict) and str(t.get("candidate_name"))==candidate]
    return rows

def economic_metrics(payload):
    scores=payload.get("scores") if isinstance(payload.get("scores"),dict) else {}
    def first(keys,default=0.0):
        for k in keys:
            if k in payload:return num(payload.get(k),default)
            if k in scores:return num(scores.get(k),default)
        return default
    return {
        "profit":first(("expected_profit","profit","projected_profit","profit_score","profitability_score"),0.0),
        "probability":first(("probability","success_probability","confidence","confidence_score"),0.0),
        "readiness":first(("readiness","readiness_score","execution_readiness"),0.0),
        "score":first(("score","total_score","composite_score","opportunity_score"),0.0),
    }

def evidence_summary(tasks):
    total=len(tasks)
    observed=[t for t in tasks if t.get("status")=="observed"]
    coverage=(len(observed)/total) if total else 0.0
    reqs={str(t.get("requirement")) for t in tasks}
    observed_reqs={str(t.get("requirement")) for t in observed}
    critical={r for r in ("provenance","corroboration","pricing","buyer_demand") if r in reqs}
    missing_critical=sorted(critical-observed_reqs)
    return {
        "total":total,
        "observed":len(observed),
        "coverage":round(coverage,4),
        "requirements":sorted(reqs),
        "observed_requirements":sorted(observed_reqs),
        "critical_requirements":sorted(critical),
        "missing_critical":missing_critical,
    }

def recompute_readiness(metrics,evidence):
    # Evidence can improve confidence/readiness, but does not manufacture profit or probability.
    evidence_component=evidence["coverage"]*40.0
    base=max(0.0,min(60.0,metrics["readiness"]))
    if metrics["probability"]>0: base+=5
    if metrics["profit"]>0: base+=5
    if evidence["missing_critical"]: base-=10
    return round(max(0.0,min(100.0,base+evidence_component)),2)

def decide(metrics,evidence,recalculated_readiness):
    if evidence["total"]==0:
        return "continue_research",["no_evidence_tasks"]
    if evidence["coverage"] < MIN_EVIDENCE_COVERAGE:
        return "continue_research",["evidence_coverage_below_threshold"]
    if evidence["missing_critical"]:
        return "continue_research",["critical_evidence_missing:"+",".join(evidence["missing_critical"])]
    if metrics["profit"] <= 0:
        return "deprioritize",["profit_not_established"]
    if metrics["probability"] <= 0:
        return "continue_research",["probability_not_established"]
    if recalculated_readiness < READINESS_THRESHOLD:
        return "continue_research",["readiness_below_threshold"]
    return "promote_to_guarded_execution",["evidence_and_economics_sufficient"]

def update_candidate(path,payload,decision,evidence,metrics,recalc):
    payload["decision_ready"] = decision=="promote_to_guarded_execution"
    payload["evidence_validation"]={
        "coverage":evidence["coverage"],
        "observed":evidence["observed"],
        "total":evidence["total"],
        "missing_critical":evidence["missing_critical"],
        "evaluated_at":time.time(),
    }
    payload["evidence_readiness_score"]=recalc
    payload["decision_status"]=decision
    payload["decision_updated_at"]=time.time()
    atomic(path,payload)

def update_packet(queue,packet,decision,reasons,evidence,metrics,recalc):
    packet["decision_closure"]={
        "decision":decision,
        "reasons":reasons,
        "evidence":evidence,
        "metrics":metrics,
        "recalculated_readiness":recalc,
        "threshold":READINESS_THRESHOLD,
        "evaluated_at":time.time(),
    }
    if decision=="promote_to_guarded_execution":
        packet["status"]="ready_for_guarded_execution"
    elif decision=="deprioritize":
        packet["status"]="deprioritized"
    else:
        packet["status"]="research_required"
    atomic(ACTION_QUEUE,queue)

def cycle():
    queue,packet=latest_packet()
    if not packet:
        state={"running":True,"healthy":True,"last_cycle_unix":time.time(),"status":"no_action_packet"}
        atomic(STATE,state);return state

    name=str(packet.get("candidate_name") or "")
    path,payload=find_candidate(name)
    if path is None or not isinstance(payload,dict):
        state={"running":True,"healthy":False,"last_cycle_unix":time.time(),"status":"candidate_not_found","candidate":name}
        atomic(STATE,state);return state

    tasks=evidence_for(name)
    evidence=evidence_summary(tasks)
    metrics=economic_metrics(payload)
    recalc=recompute_readiness(metrics,evidence)
    decision,reasons=decide(metrics,evidence,recalc)

    update_candidate(path,payload,decision,evidence,metrics,recalc)
    update_packet(queue,packet,decision,reasons,evidence,metrics,recalc)

    record={
        "ts":time.time(),
        "candidate":name,
        "decision":decision,
        "reasons":reasons,
        "evidence":evidence,
        "metrics":metrics,
        "recalculated_readiness":recalc,
        "action_packet_id":packet.get("action_packet_id"),
    }
    append_history(record)

    state={
        "running":True,
        "healthy":True,
        "last_cycle_unix":time.time(),
        "status":"decision_evaluated",
        "candidate":name,
        "decision":decision,
        "reasons":reasons,
        "evidence":evidence,
        "metrics":metrics,
        "recalculated_readiness":recalc,
        "readiness_threshold":READINESS_THRESHOLD,
    }
    atomic(STATE,state)
    return state

def run():
    interval=max(120,int(os.getenv("COMPANYOS_EVIDENCE_DECISION_INTERVAL_SECONDS","300")))
    while not STOP.exists():
        try:cycle()
        except Exception as exc:
            atomic(STATE,{"running":True,"healthy":False,"last_cycle_unix":time.time(),"status":"cycle_error","error":repr(exc)})
        time.sleep(interval)

if __name__=="__main__":
    import argparse
    a=argparse.ArgumentParser()
    a.add_argument("command",nargs="?",default="run",choices=("run","once","status","history"))
    cmd=a.parse_args().command
    if cmd=="run":run()
    elif cmd=="once":print(json.dumps(cycle(),indent=2,sort_keys=True,default=str))
    elif cmd=="history":
        print(HISTORY.read_text(encoding="utf-8") if HISTORY.exists() else "")
    else:print(json.dumps(load(STATE,{"status":"not_run"}),indent=2,sort_keys=True,default=str))
