#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory";OUT=MEM/"autonomous_ceo_cycle_report.json";STATE=MEM/"autonomous_ceo_cycle_state.json";HEALTH=MEM/"autonomous_ceo_cycle_health.json"
PIPELINE=[("opportunity_scoring",["python","companyos/opportunityscoringctl","run"]),("strategic_planning",["python","companyos/strategicexecutionctl","run"]),("agent_orchestration",["python","companyos/agentorchestrationctl","run"]),("phase25_multiagent",["python","companyos/phase25bundle2ctl","run"]),("learning_feedback",["python","companyos/learningfeedbackctl","run"]),("stalled_recovery",["python","companyos/stalledrecoveryctl","run"])]
def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def call(cmd):
    try:
        p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=2400)
        return {"success":p.returncode==0,"return_code":p.returncode,"stdout":p.stdout[-2500:],"stderr":p.stderr[-1000:]}
    except Exception as e:return {"success":False,"error":str(e)}
def run():
    steps=[];failed=[]
    for name,cmd in PIPELINE:
        r=call(cmd);steps.append({"step":name,"result":r})
        if not r.get("success"):failed.append(name)
    payload={"generated_at":now(),"failure_count":len(failed),"failed_steps":failed,"steps":steps,"cycle":"discover_score_plan_delegate_validate_learn_recover","external_authority_granted":False}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"failure_count":len(failed),"failed_steps":failed});save(HEALTH,{"healthy":not failed,"last_checked_at":now()})
    return {"success":not failed,"status":"autonomous_ceo_cycle_complete","report":payload}
print(json.dumps(run(),indent=2))
