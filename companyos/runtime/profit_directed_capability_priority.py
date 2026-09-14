from __future__ import annotations
import json, time
from pathlib import Path

ROOT=(Path.home()/"companyos").resolve()
RT=ROOT/".companyos_runtime"
BASE=RT/"capability_expansion"
QUEUE=BASE/"next_capability_queue.json"
STATE=BASE/"profit_directed_priority_state.json"
EVENTS=BASE/"profit_directed_priority_events.jsonl"

PROFIT_FILES=(
    RT/"profit_opportunity_status.json",
    RT/"profit_first_dispatcher_state.json",
    RT/"research_to_execution_bridge_state.json",
    RT/"candidate_materialization_report.json",
    RT/"profit_opportunity_ledger.json",
)
REASON_WEIGHTS={
    "missing_executable_next_action":40,
    "missing_external_evidence":32,
    "probability_unestimated":28,
    "profit_unestimated":36,
    "score_below_execution_threshold":30,
    "missing_customer":26,
    "missing_offer":30,
    "missing_pricing":34,
    "missing_sales_channel":32,
    "missing_deployment_path":20,
    "missing_validation":24,
}

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

def _profit_context():
    merged={}
    for p in PROFIT_FILES:
        x=load(p,None)
        if isinstance(x,dict): merged[p.name]=x
    return merged

def _signals(ctx):
    text=json.dumps(ctx,default=str).lower()
    found={}
    for reason,weight in REASON_WEIGHTS.items():
        if reason in text: found[reason]=weight
    return found

def _request_reason(req):
    evidence=req.get("semantic_evidence") or {}
    return str(evidence.get("reason") or req.get("reason") or "").lower()

def score_request(req,profit_signals):
    base=int(req.get("priority",50) or 50)
    reason=_request_reason(req)
    score=base
    for signal,weight in profit_signals.items():
        if signal in reason or signal in json.dumps(req,default=str).lower():
            score+=weight
    keywords={
        "profit":18,"pricing":16,"customer":14,"offer":14,"sales":14,
        "executable_next_action":20,"external_evidence":14,"probability":12,
        "readiness":12,"revenue":20,"conversion":16,"margin":18,
    }
    blob=json.dumps(req,default=str).lower()
    for k,w in keywords.items():
        if k in blob: score+=w
    if any(m in str(req.get("requested_capability","")) for m in (
        "downstream_gap_detector","capability_gap","self_evolution","recursive"
    )):
        score-=15
    return max(0,min(200,score))

def cycle():
    q=load(QUEUE,{"requests":[]})
    reqs=q.get("requests",[])
    if not isinstance(reqs,list):
        return {"ok":False,"status":"bad_queue"}
    ctx=_profit_context()
    signals=_signals(ctx)
    ranked=[]
    changed=0
    for req in reqs:
        if not isinstance(req,dict) or req.get("status")!="research_required": continue
        if req.get("execution_allowed") is not False: continue
        if req.get("external_action_allowed") is not False: continue
        if req.get("financial_action_allowed") is not False: continue
        if req.get("credential_access_allowed") is not False: continue
        if req.get("deployment_allowed") is not False: continue
        score=score_request(req,signals)
        if req.get("profit_directed_priority")!=score: changed+=1
        req["profit_directed_priority"]=score
        req["profit_directed_at"]=time.time()
        ranked.append({
            "requested_capability":req.get("requested_capability"),
            "gap_id":req.get("gap_id"),
            "score":score,
            "reason":_request_reason(req),
        })
    ranked.sort(key=lambda x:(-x["score"],str(x["requested_capability"])))
    if ranked:
        q["requests"].sort(
            key=lambda r:(
                0 if isinstance(r,dict) and r.get("status")=="research_required" else 1,
                -(r.get("profit_directed_priority",r.get("priority",0)) if isinstance(r,dict) else 0),
                str(r.get("requested_capability","")) if isinstance(r,dict) else "",
            )
        )
        atomic(QUEUE,q)
    state={
        "running":True,"healthy":True,"last_cycle_unix":time.time(),
        "profit_signal_count":len(signals),"profit_signals":signals,
        "ranked_count":len(ranked),"changed_count":changed,"top_requests":ranked[:10],
    }
    atomic(STATE,state)
    emit("profit_directed_priority_cycle",top_requests=ranked[:5],profit_signals=signals)
    return state

if __name__=="__main__":
    import argparse
    a=argparse.ArgumentParser()
    a.add_argument("command",nargs="?",default="once",choices=("once","status"))
    cmd=a.parse_args().command
    if cmd=="once": print(json.dumps(cycle(),indent=2,sort_keys=True))
    else: print(json.dumps(load(STATE,{"status":"not_run"}),indent=2,sort_keys=True))
