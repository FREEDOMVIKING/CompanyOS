#!/usr/bin/env python3
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
P=ROOT/"ceo_memory"/"ceo_external_action_queue.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load():
    try:return json.loads(P.read_text())
    except:return {"actions":[]}
def save(d):P.write_text(json.dumps(d,indent=2))

if len(sys.argv)<4 or sys.argv[1]!="submit":
    print(json.dumps({
      "success":False,
      "status":"usage",
      "usage":"submit ACTION_TYPE JSON_PAYLOAD"
    },indent=2))
    raise SystemExit(1)

action_type=sys.argv[2]
payload=json.loads(sys.argv[3])
action_id=hashlib.sha256(
    f"{now()}|{action_type}|{json.dumps(payload,sort_keys=True)}".encode()
).hexdigest()[:24]

row={
  "action_id":action_id,
  "created_at":now(),
  "source":"ceo",
  "action_type":action_type,
  "payload":payload,
  "status":"pending"
}

d=load()
d.setdefault("actions",[]).append(row)
d["updated_at"]=now()
save(d)

print(json.dumps({
  "success":True,
  "status":"phase41_action_queued",
  "action":row
},indent=2))
