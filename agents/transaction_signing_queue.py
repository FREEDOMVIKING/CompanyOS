#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
QUEUE=MEM/"transaction_proposals.json";OUT=MEM/"transaction_signing_queue.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
rows=[]
for x in load(QUEUE,{"proposals":[]}).get("proposals",[]):
    if x.get("status")=="ready_for_signing" and x.get("signing_authorized"):
        rows.append(x)
payload={"generated_at":now(),"ready_count":len(rows),"transactions":rows}
OUT.write_text(json.dumps(payload,indent=2))
print(json.dumps({"success":True,"status":"transaction_signing_queue_complete","queue":payload},indent=2))
