#!/usr/bin/env python3
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
CFG=MEM/"authority_execution_config.json";OUT=MEM/"communications_execution_queue.json"
def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):p.write_text(json.dumps(d,indent=2))
def run():
    cfg=load(CFG,{})["communications_authority"]
    payload={"generated_at":now(),"enabled":cfg.get("enabled"),"capabilities":{
      "business_email":cfg.get("automatic_business_email"),
      "customer_messaging":cfg.get("automatic_customer_messaging"),
      "api_messaging":cfg.get("automatic_api_messaging"),
      "contractual_commitments_require_owner_approval":cfg.get("contractual_commitments_require_owner_approval"),
      "mass_outreach_requires_owner_approval":cfg.get("mass_outreach_requires_owner_approval")
    },"status":"connector_ready"}
    save(OUT,payload);return {"success":True,"status":"communications_authority_complete","report":payload}
print(json.dumps(run(),indent=2))
