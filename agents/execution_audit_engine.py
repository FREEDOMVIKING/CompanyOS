#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
OUT=MEM/"execution_authority_audit.json"
def now():return datetime.now(timezone.utc).isoformat()
def load(name,d):
    try:return json.loads((MEM/name).read_text())
    except:return d
def run():
    r={"generated_at":now(),
       "financial_queue":load("financial_execution_queue.json",{"items":[]}),
       "approvals":load("owner_approval_queue.json",{"items":[]}),
       "communications":load("communications_execution_queue.json",{}),
       "publication":load("publication_authority_report.json",{}),
       "deployment":load("deployment_authority_report.json",{})}
    OUT.write_text(json.dumps(r,indent=2));return {"success":True,"status":"execution_audit_complete","report":r}
print(json.dumps(run(),indent=2))
