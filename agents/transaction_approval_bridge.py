#!/usr/bin/env python3
import json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
QUEUE=MEM/"transaction_proposals.json"

def now():return datetime.now(timezone.utc).isoformat()
def load():
    try:return json.loads(QUEUE.read_text())
    except:return {"proposals":[]}
def save(d):QUEUE.write_text(json.dumps(d,indent=2))

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a in ("approve","deny"):
    q=load();item=None
    for x in q.get("proposals",[]):
        if x.get("proposal_id")==sys.argv[2]:
            item=x
            if a=="approve":
                x["status"]="ready_for_signing";x["signing_authorized"]=True;x["owner_approved_at"]=now()
            else:
                x["status"]="denied";x["signing_authorized"]=False;x["owner_denied_at"]=now()
            break
    save(q);r={"success":bool(item),"status":"transaction_approval_updated","proposal":item}
else:
    r={"success":True,"status":"transaction_approval_status","queue":load()}
print(json.dumps(r,indent=2))
