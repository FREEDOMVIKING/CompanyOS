#!/usr/bin/env python3
import json, sys, hashlib
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
P=ROOT/"ceo_memory"/"company_goals.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def load():
    try:return json.loads(P.read_text())
    except:return {"goals":[]}

if len(sys.argv)<3 or sys.argv[1]!="add":
    print(json.dumps({
      "success":False,
      "status":"usage",
      "usage":"add JSON_GOAL"
    },indent=2))
    raise SystemExit(1)

g=json.loads(sys.argv[2])

required=["title","objective","metric","target_value"]
missing=[k for k in required if g.get(k) in (None,"")]
if missing:
    print(json.dumps({"success":False,"status":"missing_goal_fields","missing":missing},indent=2))
    raise SystemExit(1)

goal_id=g.get("goal_id") or hashlib.sha256(
    f"{now()}|{json.dumps(g,sort_keys=True)}".encode()
).hexdigest()[:24]

row={
  "goal_id":goal_id,
  "created_at":now(),
  "title":g["title"],
  "objective":g["objective"],
  "metric":g["metric"],
  "target_value":g["target_value"],
  "current_value":g.get("current_value",0),
  "deadline":g.get("deadline"),
  "priority":g.get("priority",70),
  "constraints":g.get("constraints",[]),
  "status":"active"
}

d=load()
d.setdefault("goals",[]).append(row)
d["updated_at"]=now()
P.write_text(json.dumps(d,indent=2))

print(json.dumps({
  "success":True,
  "status":"phase46_goal_added",
  "goal":row
},indent=2))
