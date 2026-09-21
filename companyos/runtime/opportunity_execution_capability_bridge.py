from __future__ import annotations
import hashlib, json, os, time
from pathlib import Path

ROOT=Path.home()/"companyos"
RT=Path.home()/".companyos_runtime"
STATE=RT/"opportunity_execution_capability_bridge_state.json"
QUEUE=RT/"profit_execution_action_queue.json"
EVENTS=RT/"opportunity_execution_capability_bridge_events.jsonl"
STOP=RT/"STOP_CONTINUOUS"
CANDIDATE_DIR=RT/"profit_first_candidates"
FEEDBACK=RT/"capability_feedback_state.json"

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

def num(v,default=0.0):
    try:return float(v)
    except Exception:return default

def active_capabilities():
    fb=load(FEEDBACK,{})
    caps=fb.get("capabilities",{}) if isinstance(fb,dict) else {}
    out=[]
    if isinstance(caps,dict):
        for cid,rec in caps.items():
            if isinstance(rec,dict) and rec.get("status")=="active":
                out.append((cid,rec))
    return out

def candidate_score(payload):
    vals=[]
    for k in ("score","composite_score","total_score","opportunity_score","profitability_score","expected_value_score","rank_score"):
        if k in payload: vals.append(num(payload.get(k),0))
    scores=payload.get("scores")
    if isinstance(scores,dict): vals += [num(v,0) for v in scores.values()]
    if vals:return sum(vals)/len(vals)
    text=json.dumps(payload,default=str).lower()
    score=0
    if any(x in text for x in ("customer","buyer","market")):score+=15
    if any(x in text for x in ("revenue","price","margin","profit")):score+=20
    if any(x in text for x in ("evidence","source","competitor")):score+=15
    return score

def load_candidates():
    rows=[]
    if not CANDIDATE_DIR.exists():return rows
    for p in CANDIDATE_DIR.glob("*.json"):
        x=load(p,None)
        if not isinstance(x,dict):continue
        name=str(x.get("name") or x.get("candidate_name") or x.get("venture_name") or p.stem)
        rows.append({"name":name,"source":str(p.relative_to(ROOT)),"payload":x,"score":round(candidate_score(x),2)})
    rows.sort(key=lambda r:r["score"],reverse=True)
    return rows

def run_capabilities(candidate):
    from companyos.runtime import capability_expansion as ce
    results=[]
    ctx={
        "profit":{"candidate_count":1,"eligible_count":1},
        "candidate":candidate["payload"],
        "opportunity":candidate["payload"],
        "qualification_rejections":[],
        "bridge":{"candidate":candidate["payload"],"accepted":1,"rejected":0},
    }
    for cid,rec in active_capabilities():
        try:
            out=ce.run_capability(cid,ctx)
            results.append({"capability_id":cid,"ok":True,"utility_score":rec.get("utility_score"),"result":out})
        except Exception as exc:
            results.append({"capability_id":cid,"ok":False,"error":repr(exc)})
    return results

def extract_actions(candidate,cap_results):
    actions=[]
    blob=json.dumps(candidate["payload"],default=str).lower()
    for row in cap_results:
        if not row.get("ok"):continue
        result=row.get("result")
        if not isinstance(result,dict):continue
        for key in ("next_action","recommended_action","action","recommended_next_action"):
            v=result.get(key)
            if isinstance(v,str) and v.strip():
                actions.append({"source":row["capability_id"],"action":v.strip(),"confidence":75})
        tb=result.get("top_bottleneck")
        if isinstance(tb,dict):
            reason=str(tb.get("reason") or "")
            if reason=="missing_executable_next_action":
                actions.append({"source":row["capability_id"],"action":"Define one measurable, reversible next step that advances this opportunity toward customer validation or revenue.","confidence":85})
            elif reason=="missing_external_evidence":
                actions.append({"source":row["capability_id"],"action":"Collect one concrete external evidence artifact for buyer demand, pricing, competition, or willingness-to-pay, then rescore the opportunity.","confidence":82})
            elif reason=="profit_unestimated":
                actions.append({"source":row["capability_id"],"action":"Estimate unit economics and expected profit using evidence-backed assumptions before execution.","confidence":80})
            elif reason=="probability_unestimated":
                actions.append({"source":row["capability_id"],"action":"Estimate success probability from observed evidence and record uncertainty before committing resources.","confidence":78})
    if not actions:
        if "customer" not in blob and "buyer" not in blob:
            actions.append({"source":"bridge_fallback","action":"Identify a concrete buyer/customer segment and one reachable validation channel.","confidence":65})
        elif "price" not in blob and "pricing" not in blob:
            actions.append({"source":"bridge_fallback","action":"Define and validate an initial price hypothesis against the target buyer.","confidence":65})
        elif "evidence" not in blob and "source" not in blob:
            actions.append({"source":"bridge_fallback","action":"Gather external evidence supporting demand, pricing, and competition before build-out.","confidence":65})
        else:
            actions.append({"source":"bridge_fallback","action":"Create the smallest reversible validation experiment with a measurable pass/fail criterion.","confidence":65})
    seen=set();uniq=[]
    for a in actions:
        key=a["action"].strip().lower()
        if key in seen:continue
        seen.add(key);uniq.append(a)
    return uniq[:5]

def build_packet(candidate,cap_results,actions):
    return {
        "candidate_name":candidate["name"],
        "candidate_source":candidate["source"],
        "candidate_score":candidate["score"],
        "created_at":time.time(),
        "status":"ready_for_guarded_execution",
        "execution_allowed":True,
        "external_action_allowed":"existing_policy_only",
        "financial_action_allowed":"existing_policy_only",
        "credential_access_allowed":"existing_policy_only",
        "deployment_allowed":"existing_policy_only",
        "capability_results":cap_results,
        "recommended_actions":actions,
        "required_execution_contract":[
            "Use the existing CompanyOS approval/safety/finance/credential/deployment gates.",
            "Prefer reversible, measurable actions.",
            "Do not fabricate evidence, buyers, revenue, pricing, or probability.",
            "Do not perform financial transactions merely to prove activity.",
            "Record measurable outcome evidence and feed it back into opportunity scoring.",
        ],
    }

def cycle():
    candidates=load_candidates()
    if not candidates:
        state={"running":True,"healthy":True,"last_cycle_unix":time.time(),"status":"no_candidates","packet_count":0}
        atomic(STATE,state);return state
    top=candidates[0]
    cap_results=run_capabilities(top)
    actions=extract_actions(top,cap_results)
    packet=build_packet(top,cap_results,actions)
    # COMPANYOS_OUTCOME_BASELINE_V18
    packet["candidate_snapshot"]=top["payload"]
    packet["candidate_metrics_before"]={
        "profit": candidate_score({"profit": top["payload"].get("expected_profit", top["payload"].get("profit", 0))}),
        "probability": float(top["payload"].get("probability", top["payload"].get("confidence", 0)) or 0),
        "readiness": float(top["payload"].get("readiness", top["payload"].get("readiness_score", 0)) or 0),
        "score": float(top.get("score", 0) or 0),
        "evidence_count": len(top["payload"].get("evidence", [])) if isinstance(top["payload"].get("evidence"), list) else 0,
    }
    q=load(QUEUE,{"actions":[]})
    arr=q.get("actions")
    if not isinstance(arr,list):arr=[]
    fingerprint=packet["candidate_name"]+"|"+json.dumps(packet["recommended_actions"],sort_keys=True)
    fid=hashlib.sha256(fingerprint.encode()).hexdigest()[:20]
    packet["action_packet_id"]=fid
    existing={x.get("action_packet_id") for x in arr if isinstance(x,dict)}
    created=False
    if fid not in existing:
        arr.append(packet);q["actions"]=arr[-100:];atomic(QUEUE,q);created=True
        emit("action_packet_created",action_packet_id=fid,candidate=packet["candidate_name"])
    state={
        "running":True,"healthy":True,"last_cycle_unix":time.time(),
        "status":"action_packet_ready","packet_created":created,"packet_count":len(arr),
        "top_candidate":packet["candidate_name"],"top_candidate_score":packet["candidate_score"],
        "active_capability_count":len(active_capabilities()),
        "recommended_actions":packet["recommended_actions"],"action_packet_id":fid,
    }
    atomic(STATE,state);return state

def run():
    interval=max(120,int(os.getenv("COMPANYOS_OPPORTUNITY_EXECUTION_BRIDGE_INTERVAL_SECONDS","300")))
    while not STOP.exists():
        try:cycle()
        except Exception as exc:
            atomic(STATE,{"running":True,"healthy":False,"last_cycle_unix":time.time(),"status":"cycle_error","error":repr(exc)})
        time.sleep(interval)

if __name__=="__main__":
    import argparse
    a=argparse.ArgumentParser()
    a.add_argument("command",nargs="?",default="run",choices=("run","once","status","queue"))
    cmd=a.parse_args().command
    if cmd=="run":run()
    elif cmd=="once":print(json.dumps(cycle(),indent=2,sort_keys=True,default=str))
    elif cmd=="queue":print(json.dumps(load(QUEUE,{"actions":[]}),indent=2,sort_keys=True,default=str))
    else:print(json.dumps(load(STATE,{"status":"not_run"}),indent=2,sort_keys=True,default=str))
