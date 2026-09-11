#!/usr/bin/env python3
import json, sys, hashlib, secrets
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
QUEUE=MEM/"owner_approval_queue.json"
STATE=MEM/"owner_approval_state.json"
HEALTH=MEM/"owner_approval_health.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def aid(seed): return hashlib.sha256((str(seed)+secrets.token_hex(4)).encode()).hexdigest()[:20]

def request(action_class, summary, payload):
    q=load(QUEUE,{"items":[]})
    item={
      "approval_id":aid(summary),
      "action_class":action_class,
      "summary":summary,
      "payload":payload,
      "status":"pending_owner_approval",
      "created_at":now()
    }
    q["items"].append(item);q["updated_at"]=now()
    save(QUEUE,q);save(STATE,{"last_request_at":now(),"pending_count":sum(1 for x in q["items"] if x["status"]=="pending_owner_approval")})
    save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return item

def set_status(approval_id,status):
    q=load(QUEUE,{"items":[]})
    found=None
    for x in q["items"]:
        if x.get("approval_id")==approval_id:
            x["status"]=status;x["resolved_at"]=now();found=x;break
    save(QUEUE,q)
    return found

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="request":
    item=request(sys.argv[2],sys.argv[3],json.loads(sys.argv[4]) if len(sys.argv)>4 else {})
    r={"success":True,"status":"approval_requested","item":item}
elif a in ("approve","deny"):
    found=set_status(sys.argv[2],"approved" if a=="approve" else "denied")
    r={"success":bool(found),"status":"approval_updated","item":found}
else:
    q=load(QUEUE,{"items":[]})
    r={"success":True,"status":"owner_approval_status","queue":q}
print(json.dumps(r,indent=2))
