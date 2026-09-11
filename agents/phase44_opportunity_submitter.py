#!/usr/bin/env python3
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
P=ROOT/"ceo_memory"/"phase44_opportunity_queue.json"

def now():return datetime.now(timezone.utc).isoformat()

def load():
    try:return json.loads(P.read_text())
    except:return {"opportunities":[]}

if len(sys.argv)<3 or sys.argv[1]!="submit":
    print(json.dumps({
      "success":False,
      "status":"usage",
      "usage":"submit JSON_OPPORTUNITY"
    },indent=2))
    raise SystemExit(1)

o=json.loads(sys.argv[2])
if not o.get("opportunity_id"):
    o["opportunity_id"]=hashlib.sha256(
      f"{now()}|{json.dumps(o,sort_keys=True)}".encode()
    ).hexdigest()[:24]

o.setdefault("status","new")
o.setdefault("created_at",now())

d=load()
d.setdefault("opportunities",[]).append(o)
d["updated_at"]=now()
P.write_text(json.dumps(d,indent=2))

print(json.dumps({
  "success":True,
  "status":"phase44_opportunity_queued",
  "opportunity":o
},indent=2))
