#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"opportunity_cycle_config.json"; STATE=MEM/"opportunity_cycle_state.json"
REPORT=MEM/"opportunity_cycle_report.json"; HEALTH=MEM/"opportunity_cycle_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def call(cmd):
    try:
        p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=600)
        return {"success":p.returncode==0,"return_code":p.returncode,
                "stdout":p.stdout[-2500:],"stderr":p.stderr[-1200:]}
    except Exception as e:return {"success":False,"error":str(e)}

STEPS=[
("run_alignment","strategic_alignment",["python","companyos/strategicalignctl","align"]),
("run_reranking","learned_reranking",["python","companyos/opportunityrerankctl","rerank"]),
("run_activation","activation",["python","companyos/opportunityactivatectl","activate"]),
("run_translation","translation",["python","companyos/opportunitytranslatectl","translate"]),
("run_queue_coordination","queue_coordination",["python","companyos/opportunityqueuectl","coordinate"]),
("run_handoff","execution_handoff",["python","companyos/actionhandoffctl","handoff"]),
("run_guarded_execution","guarded_execution",["python","companyos/opportunityexecctl","run"]),
("run_outcome_feedback","outcome_feedback",["python","companyos/opportunityoutcomectl","analyze"])
]

def cycle():
    cfg=load(CFG,{})
    results=[]
    for flag,name,cmd in STEPS:
        if cfg.get(flag,True):
            results.append({"step":name,"result":call(cmd)})
    failures=[x["step"] for x in results if not x["result"].get("success")]
    report={"generated_at":now(),"steps":results,"failure_count":len(failures),"failed_steps":failures,
            "automatic_external_write":False,"automatic_customer_contact":False,
            "automatic_publication":False,"automatic_spending":False,"automatic_code_changes":False,
            "automatic_merge":False,"automatic_deploy":False,"automatic_destructive_actions":False}
    save(REPORT,report)
    save(STATE,{"last_cycle_at":now(),"failure_count":len(failures),"failed_steps":failures})
    save(HEALTH,{"healthy":len(failures)==0,"last_checked_at":now(),"failure_count":len(failures)})
    return {"success":len(failures)==0,"status":"adaptive_opportunity_cycle_complete","report":report}

def status():
    return {"success":True,"status":"adaptive_opportunity_cycle_status",
            "state":load(STATE,{}),"health":load(HEALTH,{}),"report":load(REPORT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=cycle() if a=="run" else status() if a=="status" else {"success":False,"allowed":["run","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
