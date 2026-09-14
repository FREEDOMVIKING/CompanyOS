#!/usr/bin/env python3
import json,os,sys,urllib.request,urllib.error
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"specialist_runtime_config.json"
WORK=MEM/"governed_internal_work_results.json"
OUT=MEM/"specialist_runtime_results.json"
STATE=MEM/"specialist_runtime_state.json"
REPORT=MEM/"specialist_runtime_report.json"
HEALTH=MEM/"specialist_runtime_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def call_model(cfg,item):
    key=os.getenv(cfg.get("api_key_env","OPENAI_API_KEY"),"").strip()
    if not key:return None,"missing_api_key"
    base=cfg.get("base_url","https://api.openai.com/v1").rstrip("/")
    url=base+"/chat/completions"
    system=("You are a specialist worker inside CompanyOS. Perform internal, non-destructive reasoning only. "
            "Do not claim to have contacted people, spent money, deployed, published, modified external systems, "
            "or performed actions you cannot verify. Return ONLY valid JSON with keys: summary, findings, "
            "recommendations, risks, next_internal_actions, confidence. confidence must be 0 to 1.")
    prompt=json.dumps({
      "action_type":item.get("action_type"),
      "instruction":item.get("instruction"),
      "opportunity_id":item.get("opportunity_id"),
      "execution_boundary":"internal_non_destructive_only"
    })
    body=json.dumps({"model":cfg.get("model"),"temperature":0.2,
      "messages":[{"role":"system","content":system},{"role":"user","content":prompt}],
      "response_format":{"type":"json_object"}}).encode()
    req=urllib.request.Request(url,data=body,headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=int(cfg.get("timeout_seconds",120))) as r:
            data=json.loads(r.read().decode())
        text=data["choices"][0]["message"]["content"]
        return json.loads(text),None
    except Exception as e:return None,str(e)

def run():
    cfg=load(CFG,{})
    rows=load(WORK,{}).get("results",[])
    previous=load(OUT,{"results":[]}).get("results",[])
    done={x.get("work_id") for x in previous if x.get("status")=="completed"}
    maximum=int(cfg.get("maximum_items_per_cycle",5));completed=[];pending=[]

    for item in rows:
        if len(completed)>=maximum:break
        if item.get("status")!="prepared_for_specialist_runtime" or item.get("work_id") in done:continue
        actual,error=call_model(cfg,item)
        if error:
            pending.append({"work_id":item.get("work_id"),"status":"pending","reason":error})
            continue
        result={
          "work_id":item.get("work_id"),"plan_id":item.get("plan_id"),
          "decision_id":item.get("decision_id"),"opportunity_id":item.get("opportunity_id"),
          "action_type":item.get("action_type"),"status":"completed",
          "actual_result":actual,"completed_at":now(),
          "execution_boundary":"internal_non_destructive_only"
        }
        previous.append(result);completed.append(result)

    save(OUT,{"generated_at":now(),"result_count":len(previous),"results":previous})
    report={"generated_at":now(),"completed_count":len(completed),"pending_count":len(pending),
      "completed":completed,"pending":pending,
      "automatic_external_write":False,"automatic_customer_contact":False,"automatic_publication":False,
      "automatic_spending":False,"automatic_fund_transfer":False,"automatic_code_changes":False,
      "automatic_merge":False,"automatic_deploy":False,"automatic_destructive_actions":False}
    save(REPORT,report);save(STATE,{"last_run_at":now(),"completed_count":len(completed),"pending_count":len(pending)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"provider":cfg.get("provider"),
      "api_key_available":bool(os.getenv(cfg.get("api_key_env","OPENAI_API_KEY"),"").strip())})
    return {"success":True,"status":"specialist_runtime_cycle_complete","report":report}

def status():
    cfg=load(CFG,{})
    return {"success":True,"status":"specialist_runtime_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(REPORT,{}),"config":{
        "provider":cfg.get("provider"),"model":cfg.get("model"),"base_url":cfg.get("base_url"),
        "api_key_env":cfg.get("api_key_env")}}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=run() if a=="run" else status() if a=="status" else {"success":False,"allowed":["run","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
