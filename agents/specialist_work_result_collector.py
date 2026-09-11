#!/usr/bin/env python3
import json,sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"specialist_result_config.json"; QUEUE=MEM/"multiagent_work_queue.json"
STATE=MEM/"specialist_result_state.json"; REPORT=MEM/"specialist_result_report.json"
HEALTH=MEM/"specialist_result_health.json"; OUT=MEM/"specialist_work_results.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def collect():
    cfg=load(CFG,{})
    items=load(QUEUE,{}).get("work_items",[])
    maximum=int(cfg.get("maximum_results_per_cycle",10))
    allowed=set(cfg.get("allowed_work_modes",[]))
    results=[];blocked=[]

    for item in items[:maximum]:
        mode=item.get("work_mode","analyze")
        if mode not in allowed:
            blocked.append({"work_id":item.get("work_id"),"reason":"work_mode_not_allowed"})
            continue
        results.append({
          "result_id":f"{item.get('work_id')}-result",
          "work_id":item.get("work_id"),"opportunity_id":item.get("opportunity_id"),
          "title":item.get("title"),"specialist_role":item.get("specialist_role"),
          "specialist":item.get("specialist"),"work_mode":mode,
          "status":"ready_for_internal_specialist_processing",
          "requested_output":{
            "summary":True,"findings":True,"recommendations":True,
            "risks":True,"next_internal_actions":True
          },
          "execution_boundary":"internal_non_destructive_only",
          "created_at":now()
        })

    payload={"generated_at":now(),"result_request_count":len(results),"results":results}
    save(OUT,payload)
    report={"generated_at":now(),"prepared_count":len(results),"blocked_count":len(blocked),
      "prepared":results,"blocked":blocked,
      "automatic_external_write":False,"automatic_customer_contact":False,"automatic_publication":False,
      "automatic_spending":False,"automatic_fund_transfer":False,"automatic_code_changes":False,
      "automatic_merge":False,"automatic_deploy":False,"automatic_destructive_actions":False}
    save(REPORT,report);save(STATE,{"last_collected_at":now(),"prepared_count":len(results),"blocked_count":len(blocked)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"prepared_count":len(results)})
    return {"success":True,"status":"specialist_work_result_collection_complete","report":report}

def status():
    return {"success":True,"status":"specialist_result_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(REPORT,{}),"results":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=collect() if a=="collect" else status() if a=="status" else {"success":False,"allowed":["collect","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
