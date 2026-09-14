from __future__ import annotations
import hashlib, json, os, re, time, traceback
from pathlib import Path

ROOT=(Path.home()/"companyos").resolve()
RT=ROOT/".companyos_runtime"
BASE=RT/"capability_expansion"
QUEUE=BASE/"next_capability_queue.json"
STATE=BASE/"semantic_bridge_state.json"
EVENTS=BASE/"semantic_bridge_events.jsonl"
STOP=RT/"STOP_CONTINUOUS"

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

def slug(value):
    s=re.sub(r"[^a-zA-Z0-9_]+","_",str(value or "")).strip("_").lower()
    return re.sub(r"_+","_",s)

SPECIAL_MAP={
    "missing_executable_next_action":"executable_next_action_planner",
    "missing_external_evidence":"external_evidence_requirements_analyzer",
    "probability_unestimated":"probability_estimator",
    "profit_unestimated":"profit_estimator",
    "score_below_execution_threshold":"execution_readiness_improver",
    "missing_next_action":"next_action_planner",
    "missing_evidence":"evidence_gap_planner",
}

def requested_capability_for(reason):
    r=slug(reason)
    if r in SPECIAL_MAP:return SPECIAL_MAP[r]
    for prefix in ("missing_","unresolved_","weak_"):
        if r.startswith(prefix):
            r=r[len(prefix):]
            break
    if not r:r="downstream_bottleneck"
    if r.endswith("_planner") or r.endswith("_analyzer") or r.endswith("_estimator"):
        return r
    return r+"_resolver"

def _extract_result(req):
    execution=req.get("execution")
    if not isinstance(execution,dict):return {}
    result=execution.get("result")
    return result if isinstance(result,dict) else {}

def _signals_from_result(result):
    out=[]
    tb=result.get("top_bottleneck")
    if isinstance(tb,dict):
        reason=tb.get("reason") or tb.get("kind") or tb.get("id")
        unresolved=tb.get("unresolved",True)
        if reason and unresolved is not False:
            out.append({
                "reason":str(reason),
                "severity":float(tb.get("severity",0) or 0),
                "detail":tb,
                "source":"top_bottleneck",
            })
    bottlenecks=result.get("bottlenecks")
    if isinstance(bottlenecks,list):
        for b in bottlenecks:
            if not isinstance(b,dict):continue
            if b.get("unresolved",True) is False:continue
            reason=b.get("reason") or b.get("kind") or b.get("id")
            if reason:
                out.append({
                    "reason":str(reason),
                    "severity":float(b.get("severity",0) or 0),
                    "detail":b,
                    "source":"bottlenecks",
                })
    # Generic semantic fallback for capability outputs that report unresolved items.
    unresolved=result.get("unresolved")
    if isinstance(unresolved,list):
        for x in unresolved:
            if isinstance(x,str):
                out.append({"reason":x,"severity":0.0,"detail":{"reason":x},"source":"unresolved"})
            elif isinstance(x,dict):
                reason=x.get("reason") or x.get("kind") or x.get("id")
                if reason:
                    out.append({"reason":str(reason),"severity":float(x.get("severity",0) or 0),"detail":x,"source":"unresolved"})
    # De-duplicate by semantic reason; highest severity wins.
    best={}
    for s in out:
        k=slug(s["reason"])
        if not k:continue
        if k not in best or s["severity"]>best[k]["severity"]:
            best[k]=s
    return sorted(best.values(),key=lambda x:(-x["severity"],slug(x["reason"])))

def _existing_keys(requests):
    keys=set()
    caps=set()
    for r in requests:
        if not isinstance(r,dict):continue
        if r.get("semantic_key"):keys.add(str(r["semantic_key"]))
        if r.get("requested_capability"):caps.add(str(r["requested_capability"]))
    return keys,caps

def _request(source_req,signal):
    source_capability=str(
        source_req.get("requested_capability")
        or source_req.get("source_capability")
        or "generated_capability"
    )
    reason=slug(signal["reason"])
    requested=requested_capability_for(reason)
    semantic_key=hashlib.sha256(
        (source_capability+"|"+reason+"|"+requested).encode()
    ).hexdigest()[:24]
    return {
        "gap_id":"semantic-"+semantic_key,
        "semantic_key":semantic_key,
        "gap_type":"semantic_output_bottleneck",
        "source_capability":source_capability,
        "requested_capability":requested,
        "reason":(
            f"{source_capability} reported unresolved bottleneck "
            f"'{reason}'. Build a safe analytical capability that converts this "
            f"finding into deterministic internal planning guidance."
        ),
        "priority":max(70,min(99,int(70+signal.get("severity",0)))),
        "status":"research_required",
        "created_at":time.time(),
        "execution_allowed":False,
        "external_action_allowed":False,
        "financial_action_allowed":False,
        "credential_access_allowed":False,
        "deployment_allowed":False,
        "semantic_evidence":{
            "reason":reason,
            "severity":signal.get("severity",0),
            "source":signal.get("source"),
            "detail":signal.get("detail"),
        },
        "generation_contract":{
            "must_be_new_capability":True,
            "must_have_tests":True,
            "must_pass_isolated_validation":True,
            "must_not_duplicate_source":True,
            "promotion_requires_existing_expansion_pipeline":True,
        },
    }

def cycle():
    queue=load(QUEUE,{"requests":[]})
    requests=queue.get("requests")
    if not isinstance(requests,list):
        return {"ok":False,"status":"bad_queue","reason":"requests_not_list"}

    existing_keys,existing_caps=_existing_keys(requests)
    candidates=[]
    for req in requests:
        if not isinstance(req,dict):continue
        if req.get("status")!="completed":continue
        result=_extract_result(req)
        if not result:continue
        for signal in _signals_from_result(result):
            new=_request(req,signal)
            # Do not duplicate an existing semantic request or capability request.
            if new["semantic_key"] in existing_keys:continue
            if new["requested_capability"] in existing_caps:continue
            candidates.append(new)

    candidates.sort(key=lambda r:(-int(r.get("priority",0)),r.get("requested_capability","")))
    created=[]
    # One semantic child per cycle prevents runaway fan-out.
    if candidates:
        item=candidates[0]
        requests.append(item)
        created.append(item)
        atomic(QUEUE,queue)
        emit(
            "semantic_request_created",
            source_capability=item.get("source_capability"),
            requested_capability=item.get("requested_capability"),
            reason=(item.get("semantic_evidence") or {}).get("reason"),
            gap_id=item.get("gap_id"),
        )

    state={
        "running":True,
        "healthy":True,
        "last_cycle_unix":time.time(),
        "completed_requests_scanned":sum(1 for r in requests if isinstance(r,dict) and r.get("status")=="completed"),
        "semantic_candidates":len(candidates),
        "created_count":len(created),
        "created":created,
    }
    atomic(STATE,state)
    return state

def run():
    interval=max(120,int(os.getenv("COMPANYOS_SEMANTIC_CAPABILITY_BRIDGE_INTERVAL_SECONDS","300")))
    while not STOP.exists():
        try:cycle()
        except Exception as exc:
            atomic(STATE,{"running":True,"healthy":False,"last_cycle_unix":time.time(),"error":repr(exc)})
            emit("cycle_exception",error=repr(exc),traceback=traceback.format_exc()[-4000:])
        time.sleep(interval)

if __name__=="__main__":
    import argparse
    a=argparse.ArgumentParser()
    a.add_argument("command",nargs="?",default="run",choices=("run","once","status"))
    cmd=a.parse_args().command
    if cmd=="run":run()
    elif cmd=="once":print(json.dumps(cycle(),indent=2,sort_keys=True,default=str))
    else:print(json.dumps(load(STATE,{"status":"not_run"}),indent=2,sort_keys=True,default=str))
