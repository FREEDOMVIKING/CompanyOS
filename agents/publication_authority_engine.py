#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
CFG=MEM/"authority_execution_config.json";OUT=MEM/"publication_authority_report.json"
def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def run():
    c=load(CFG,{})["publication_authority"]
    r={"generated_at":now(),"enabled":c.get("enabled"),"automatic_publication":c.get("automatic_publication"),
       "allowed_targets":c.get("allowed_targets",[]),"paid_ad_campaigns_require_owner_approval":c.get("paid_ad_campaigns_require_owner_approval"),
       "regulated_claims_require_owner_approval":c.get("regulated_claims_require_owner_approval")}
    OUT.write_text(json.dumps(r,indent=2));return {"success":True,"status":"publication_authority_complete","report":r}
print(json.dumps(run(),indent=2))
