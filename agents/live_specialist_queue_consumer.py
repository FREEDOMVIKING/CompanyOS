#!/usr/bin/env python3
import json,sys,os,urllib.request
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"live_specialist_consumer_config.json"
RUNTIME_CFG=MEM/"specialist_runtime_config.json"
QUEUE=MEM/"specialist_runtime_input_queue.json"
RESULTS=MEM/"specialist_runtime_results.json"
STATE=MEM/"live_specialist_consumer_state.json"
REPORT=MEM/"live_specialist_consumer_report.json"
HEALTH=MEM/"live_specialist_consumer_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def call_model(cfg,item):
    key=os.getenv(cfg.get("api_key_env","OPENROUTER_API_KEY"),"").strip()
    if not key:return None,"missing_api_key"
    url=cfg.get("base_url","https://openrouter.ai/api/v1").rstrip("/")+"/chat/completions"
    system=("You are a CompanyOS specialist. Perform internal, non-destructive reasoning only. "
            "Return ONLY JSON with keys summary, findings, recommendations, risks, next_internal_actions, confidence. "
            "Do not claim external actions were performed.")
    body=json.dumps({
      "model":cfg.get("model","openrouter/free"),
      "temperature":0.2,
      "messages":[
        {"role":"system","content":system},
        {"role":"user","content":json.dumps({
          "action_type":item.get("action_type"),
          "instruction":item.get("instruction"),
          "opportunity_id":item.get("opportunity_id"),
          "execution_boundary":"internal_non_destructive_only"
        })}
      ]
    }).encode()
    req=urllib.request.Request(url,data=body,headers={
      "Authorization":"Bearer "+key,
      "Content-Type":"application/json"
    })
    try:
        with urllib.request.urlopen(req,timeout=int(cfg.get("timeout_seconds",120))) as r:
            data=json.loads(r.read().decode())
        text=data["choices"][0]["message"]["content"]
        try: parsed=json.loads(text)
        except: parsed={
          "summary":text,"findings":[],"recommendations":[],"risks":[],
          "next_internal_actions":[],"confidence":0.5
        }
        return parsed,None
    except Exception as e:return None,str(e)

def run():
    cfg=load(CFG,{})
    runtime=load(RUNTIME_CFG,{})
    q=load(QUEUE,{"tasks":[]});tasks=q.get("tasks",[])
    result_doc=load(RESULTS,{"results":[]});results=result_doc.get("results",[])
    completed_ids={x.get("work_id") for x in results if x.get("status")=="completed"}
    allowed=set(cfg.get("allowed_statuses",["queued_for_live_specialist"]))
    maximum=int(cfg.get("maximum_tasks_per_cycle",5))
    completed=[];pending=[]

    for item in tasks:
        if len(completed)>=maximum:break
        if item.get("status") not in allowed:continue
        wid=item.get("work_id")
        if wid in completed_ids:
            item["status"]="completed";continue
        actual,error=call_model(runtime,item)
        if error:
            item["status"]="pending_retry"
            item["last_error"]=error
            item["last_attempt_at"]=now()
            pending.append({"work_id":wid,"reason":error})
            continue
        result={
          "work_id":wid,
          "plan_id":item.get("plan_id"),
          "decision_id":item.get("decision_id"),
          "opportunity_id":item.get("opportunity_id"),
          "action_type":item.get("action_type"),
          "status":"completed",
          "actual_result":actual,
          "completed_at":now(),
          "execution_boundary":"internal_non_destructive_only"
        }
        results.append(result);completed.append(result);completed_ids.add(wid)
        item["status"]="completed";item["completed_at"]=now()

    save(QUEUE,{"generated_at":now(),"task_count":len(tasks),"tasks":tasks})
    save(RESULTS,{"generated_at":now(),"result_count":len(results),"results":results})
    report={
      "generated_at":now(),"completed_count":len(completed),"pending_count":len(pending),
      "completed":completed,"pending":pending,
      "automatic_external_write":False,"automatic_customer_contact":False,"automatic_publication":False,
      "automatic_spending":False,"automatic_fund_transfer":False,"automatic_code_changes":False,
      "automatic_merge":False,"automatic_deploy":False,"automatic_destructive_actions":False
    }
    save(REPORT,report)
    save(STATE,{"last_run_at":now(),"completed_count":len(completed),"pending_count":len(pending)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"completed_count":len(completed),
      "api_key_available":bool(os.getenv(runtime.get("api_key_env","OPENROUTER_API_KEY"),"").strip())})
    return {"success":True,"status":"live_specialist_queue_consumer_complete","report":report}

def status():
    return {"success":True,"status":"live_specialist_queue_consumer_status",
      "state":load(STATE,{}),"health":load(HEALTH,{}),"report":load(REPORT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=run() if a=="run" else status() if a=="status" else {"success":False,"allowed":["run","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
