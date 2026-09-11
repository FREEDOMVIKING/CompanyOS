#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
CFG=MEM/"authority_execution_config.json";OUT=MEM/"deployment_authority_report.json"
def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def run():
    c=load(CFG,{})["deployment_authority"]
    r={"generated_at":now(),"enabled":c.get("enabled"),
       "automatic_deploy_to_approved_targets":c.get("automatic_deploy_to_approved_targets"),
       "approved_targets":c.get("approved_targets",[]),
       "require_tests_before_deploy":c.get("require_tests_before_deploy"),
       "require_health_check_after_deploy":c.get("require_health_check_after_deploy"),
       "automatic_rollback_on_failure":c.get("automatic_rollback_on_failure"),
       "new_production_target_requires_owner_approval":c.get("new_production_target_requires_owner_approval")}
    OUT.write_text(json.dumps(r,indent=2));return {"success":True,"status":"deployment_authority_complete","report":r}
print(json.dumps(run(),indent=2))
