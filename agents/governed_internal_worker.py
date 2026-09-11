#!/usr/bin/env python3
import json,sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"governed_worker_config.json"; QUEUE=MEM/"governed_internal_work_queue.json"
RESULTS=MEM/"governed_internal_work_results.json"; STATE=MEM/"governed_worker_state.json"
REPORT=MEM/"governed_worker_report.json"; HEALTH=MEM/"governed_worker_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def process_item(item):
    kind=item.get("action_type")
    instruction=str(item.get("instruction") or "").strip()
    # This worker performs deterministic internal processing only.
    # It does not claim LLM/research work occurred when no real runtime is connected.
    return {
      "work_id":item.get("work_id"),"plan_id":item.get("plan_id"),
      "decision_id":item.get("decision_id"),"opportunity_id":item.get("opportunity_id"),
      "action_type":kind,"instruction":instruction,
      "status":"prepared_for_specialist_runtime",
      "worker_output":{
        "normalized_instruction":instruction,
        "required_capability":kind,
        "execution_boundary":"internal_non_destructive_only",
        "next_state":"awaiting_real_specialist_execution"
      },
      "processed_at":now()
    }

def run():
    cfg=load(CFG,{})
    q=load(QUEUE,{"work_items":[]});items=q.get("work_items",[])
    old=load(RESULTS,{"results":[]});results=old.get("results",[])
    result_ids={x.get("work_id") for x in results}
    maximum=int(cfg.get("maximum_items_per_cycle",10));max_attempts=int(cfg.get("maximum_attempts",3))
    allowed_auth=set(cfg.get("allowed_authority",[]));allowed_types=set(cfg.get("allowed_action_types",[]))
    processed=[];blocked=[]

    for item in items:
        if len(processed)>=maximum:break
        if item.get("status")!="queued":continue
        if item.get("work_id") in result_ids:
            item["status"]="prepared_for_specialist_runtime";continue
        reasons=[]
        if item.get("execution_authority") not in allowed_auth:reasons.append("authority_not_allowed")
        if item.get("action_type") not in allowed_types:reasons.append("action_type_not_allowed")
        if int(item.get("attempts",0) or 0)>=max_attempts:reasons.append("maximum_attempts_reached")
        item["attempts"]=int(item.get("attempts",0) or 0)+1
        if reasons:
            item["status"]="blocked";item["block_reasons"]=reasons
            blocked.append({"work_id":item.get("work_id"),"reasons":reasons});continue
        result=process_item(item);results.append(result);processed.append(result)
        item["status"]="prepared_for_specialist_runtime";item["last_processed_at"]=now()

    q["generated_at"]=now();q["work_items"]=items;save(QUEUE,q)
    save(RESULTS,{"generated_at":now(),"result_count":len(results),"results":results})
    report={"generated_at":now(),"processed_count":len(processed),"blocked_count":len(blocked),
      "processed":processed,"blocked":blocked,
      "automatic_external_write":False,"automatic_customer_contact":False,"automatic_publication":False,
      "automatic_spending":False,"automatic_fund_transfer":False,"automatic_code_changes":False,
      "automatic_merge":False,"automatic_deploy":False,"automatic_destructive_actions":False}
    save(REPORT,report);save(STATE,{"last_run_at":now(),"processed_count":len(processed),"blocked_count":len(blocked)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"processed_count":len(processed)})
    return {"success":True,"status":"governed_internal_worker_cycle_complete","report":report}

def status():
    return {"success":True,"status":"governed_internal_worker_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(REPORT,{}),"results":load(RESULTS,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=run() if a=="run" else status() if a=="status" else {"success":False,"allowed":["run","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
