from __future__ import annotations
import json, os, time, traceback
from pathlib import Path

ROOT=(Path.home()/"companyos").resolve()
RT=ROOT/".companyos_runtime"
BASE=RT/"capability_expansion"
QUEUE=BASE/"next_capability_queue.json"
STATE=BASE/"request_executor_state.json"
EVENTS=BASE/"request_executor_events.jsonl"
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

def _eligible(req):
    if not isinstance(req,dict): return False,"not_dict"
    if req.get("status")!="research_required": return False,"status_not_research_required"
    checks=("execution_allowed","external_action_allowed","financial_action_allowed","credential_access_allowed","deployment_allowed")
    for key in checks:
        if req.get(key) is not False:return False,key+"_not_false"
    contract=req.get("generation_contract") or {}
    for key in ("must_be_new_capability","must_have_tests","must_pass_isolated_validation","must_not_duplicate_source","promotion_requires_existing_expansion_pipeline"):
        if contract.get(key) is not True:return False,"contract_missing:"+key
    if not req.get("requested_capability"):return False,"requested_capability_missing"
    return True,"ok"

def _replacement_capability_id(req):
    text=" ".join(str(req.get(k) or "") for k in ("gap_type","reason","requested_capability","gap_id")).lower()
    mapping=(
        (("missing_executable_next_action","executable next action"),"executable_next_action_planner"),
        (("missing_external_evidence","external evidence"),"external_evidence_requirements_analyzer"),
        (("profit_unestimated","profit unestimated","profitability"),"profitability_estimator"),
        (("probability_unestimated","probability unestimated"),"probability_estimator"),
        (("missing_revenue_evidence","revenue evidence"),"revenue_evidence_analyzer"),
        (("qualification","candidate gap","execution-qualified"),"candidate_gap_ranker"),
    )
    for needles,cid in mapping:
        if any(n in text for n in needles):
            return cid
    return "semantic_gap_resolution_analyzer"

def _gap(req):
    cid=str(req["requested_capability"])
    return {"id":cid,"title":cid.replace("_"," ").title(),"reason":str(req.get("reason") or "Compounding capability request"),"source_capability":req.get("source_capability"),"gap_type":req.get("gap_type"),"gap_id":req.get("gap_id")}

def _retry_or_reject(queue,index,req,result,**details):
    attempts=int(req.get("generation_retry_count") or 0)+1
    max_attempts=max(1,int(os.getenv("COMPANYOS_CAPABILITY_GENERATION_MAX_RETRIES","3")))
    updates=dict(details)
    updates["result"]=result
    updates["generation_retry_count"]=attempts
    updates["last_attempt"]=result
    if attempts < max_attempts:
        updates["status"]="research_required"
        updates["retry_after_unix"]=time.time()
        updates["retry_reason"]="candidate_generation_or_validation_failed"
        emit("capability_retry_queued",
             capability=req.get("requested_capability"),
             gap_id=req.get("gap_id"),
             attempt=attempts,
             reason=result)
        _update(queue,index,**updates)
        return {"ok":True,"status":"retry_queued","reason":result,"attempt":attempts}
    updates["status"]="rejected_terminal"
    updates["rejected_at"]=time.time()
    emit("capability_retry_exhausted",
         capability=req.get("requested_capability"),
         gap_id=req.get("gap_id"),
         attempts=attempts,
         reason=result)
    _update(queue,index,**updates)
    return {"ok":False,"status":"retry_exhausted","reason":result,"attempts":attempts}

def _context(req):
    return {
        "compounding_request":req,
        "capability_feedback":load(RT/"capability_feedback_state.json",{}),
        "diagnostics":load(RT/"autonomous_diagnostics_state.json",{}),
        "profit":load(RT/"profit_opportunity_status.json",{}),
    }

def _update(queue,index,**updates):
    queue["requests"][index].update(updates)
    queue["requests"][index]["updated_at"]=time.time()
    atomic(QUEUE,queue)

def _context_fingerprint(req):
    import hashlib
    ctx=_context(req)
    cr=ctx.get("compounding_request")
    if isinstance(cr,dict):
        cr=dict(cr)
        for k in ("status","updated_at","started_at","completed_at","last_attempt","generation","execution","promotion","result","error","candidate_id","retriggered_at","last_context_fingerprint"):
            cr.pop(k,None)
        ctx["compounding_request"]=cr
    raw=json.dumps(ctx,sort_keys=True,default=str,separators=(",",":"))
    return hashlib.sha256(raw.encode()).hexdigest()

def _retrigger_stale_completed(queue):
    now=time.time()
    reopened=0
    baseline_changed=False
    for req in queue.get("requests",[]):
        if not isinstance(req,dict) or req.get("status")!="completed" or not req.get("requested_capability"):
            continue
        fp=_context_fingerprint(req)
        previous=req.get("last_context_fingerprint")
        if not previous:
            req["last_context_fingerprint"]=fp
            baseline_changed=True
            continue
        if previous==fp:
            continue
        req["status"]="research_required"
        req["retriggered_at"]=now
        req["retrigger_reason"]="runtime_evidence_changed"
        req["last_context_fingerprint"]=fp
        reopened+=1
        emit("completed_request_retriggered",capability=req.get("requested_capability"),gap_id=req.get("gap_id"))
    if reopened or baseline_changed:
        atomic(QUEUE,queue)
    return reopened

def process_one():
    from companyos.runtime import capability_expansion as ce
    queue=load(QUEUE,{"requests":[]})
    _retrigger_stale_completed(queue)
    queue=load(QUEUE,{"requests":[]})
    reqs=queue.get("requests",[])
    if not isinstance(reqs,list):
        return {"ok":False,"status":"bad_queue"}

    selected=None
    for i,req in enumerate(reqs):
        ok,_=_eligible(req)
        if ok:
            selected=(i,req)
            break
    if selected is None:
        return {"ok":True,"status":"idle","reason":"no_eligible_research_required_request"}

    i,req=selected

    original_cid=str(req.get("requested_capability") or "")
    try:
        ce.canonical_paths(original_cid)
    except Exception as exc:
        replacement=_replacement_capability_id(req)
        try:
            ce.canonical_paths(replacement)
        except Exception:
            replacement="semantic_gap_resolution_analyzer"
        queue=load(QUEUE,{"requests":[]})
        _update(queue,i,
                status="research_required",
                requested_capability=replacement,
                recovered_from_capability_id=original_cid,
                recovery_reason="invalid_or_junk_capability_id",
                recovery_error=repr(exc),
                recovered_at=time.time())
        emit("junk_capability_id_recovered",
             original=original_cid,
             replacement=replacement,
             gap_id=req.get("gap_id"))
        queue=load(QUEUE,{"requests":[]})
        req=queue["requests"][i]

    gap=_gap(req); cid=gap["id"]
    inv=ce.capability_inventory()

    if cid in inv:
        try:
            execution=ce.run_capability(cid,_context(req))
            _update(queue,i,status="completed",result="existing_capability_used",execution=execution,completed_at=time.time(),last_context_fingerprint=_context_fingerprint(req))
            emit("completed_existing",capability=cid,gap_id=req.get("gap_id"))
            return {"ok":True,"status":"completed_existing","capability":cid}
        except Exception as exc:
            queue=load(QUEUE,{"requests":[]})
            return _retry_or_reject(queue,i,req,"existing_capability_failed",error=repr(exc))

    _update(queue,i,status="generating",started_at=time.time())
    ctx=_context(req)
    gen=ce.model_plan(gap,ctx)
    queue=load(QUEUE,{"requests":[]})
    if not gen.get("ok"):
        return _retry_or_reject(queue,i,req,"generation_failed",generation=gen)

    module_content,_,shape=ce._classify_generated_contents(gen.get("plan") or {},cid)
    if shape:
        queue=load(QUEUE,{"requests":[]})
        return _retry_or_reject(queue,i,req,"generation_shape_invalid",errors=shape)

    dup_fn=getattr(ce,"_is_duplicate_generated_source",None)
    if callable(dup_fn) and module_content:
        is_dup,dup_id=dup_fn(module_content)
        if is_dup:
            queue=load(QUEUE,{"requests":[]})
            _update(queue,i,status="rejected",result="duplicate_capability",duplicate_of=dup_id)
            emit("duplicate_rejected",capability=cid,duplicate_of=dup_id)
            return {"ok":True,"status":"duplicate_rejected","duplicate_of":dup_id}

    candidate_id,stage,errors=ce.stage_plan(gap,gen["plan"])
    queue=load(QUEUE,{"requests":[]})
    if errors:
        return _retry_or_reject(queue,i,req,"validation_failed",
                                candidate_id=candidate_id,errors=errors)

    ok,tests=ce.test_stage(stage,cid)
    queue=load(QUEUE,{"requests":[]})
    if not ok:
        return _retry_or_reject(queue,i,req,"tests_failed",
                                candidate_id=candidate_id,tests=tests)

    receipt=ce.promote(stage,cid,candidate_id)
    try:
        execution=ce.run_capability(cid,ctx)
    except Exception as exc:
        ce.rollback(cid)
        queue=load(QUEUE,{"requests":[]})
        return _retry_or_reject(queue,i,req,"canary_failed_rolled_back",
                                candidate_id=candidate_id,error=repr(exc))

    queue=load(QUEUE,{"requests":[]})
    _update(queue,i,status="completed",result="capability_promoted_and_used",candidate_id=candidate_id,promotion=receipt,execution=execution,completed_at=time.time(),last_context_fingerprint=_context_fingerprint(req))
    emit("completed_promoted",capability=cid,candidate_id=candidate_id,gap_id=req.get("gap_id"))
    return {"ok":True,"status":"capability_promoted_and_used","capability":cid,"candidate_id":candidate_id}

def cycle():
    result=process_one()
    state={"running":True,"last_cycle_unix":time.time(),"result":result}
    atomic(STATE,state)
    return state

def run():
    interval=max(120,int(os.getenv("COMPANYOS_CAPABILITY_REQUEST_EXECUTOR_INTERVAL_SECONDS","300")))
    while not STOP.exists():
        try:cycle()
        except Exception as exc:
            atomic(STATE,{"running":True,"last_cycle_unix":time.time(),"result":{"ok":False,"status":"cycle_exception","error":repr(exc)}})
            emit("cycle_exception",error=repr(exc),traceback=traceback.format_exc()[-4000:])
        time.sleep(interval)

if __name__=="__main__":
    import argparse
    a=argparse.ArgumentParser();a.add_argument("command",nargs="?",default="run",choices=("run","once","status"));cmd=a.parse_args().command
    if cmd=="run":run()
    elif cmd=="once":print(json.dumps(cycle(),indent=2,sort_keys=True,default=str))
    else:print(json.dumps(load(STATE,{"status":"not_run"}),indent=2,sort_keys=True,default=str))
