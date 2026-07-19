#!/usr/bin/env python3
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
P=ROOT/"ceo_memory"/"ceo_production_decisions.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def load():
    try:return json.loads(P.read_text())
    except:return {"decisions":[]}

def save(d):
    P.write_text(json.dumps(d,indent=2))

if len(sys.argv)<8:
    print(json.dumps({
      "success":False,
      "status":"usage",
      "usage":"submit CHAIN ASSET DESTINATION AMOUNT_NATIVE AMOUNT_USD REASON"
    },indent=2))
    raise SystemExit(1)

a=sys.argv[1]
if a!="submit":
    print(json.dumps({"success":False,"status":"unknown_action"},indent=2))
    raise SystemExit(1)

chain,asset,dest=sys.argv[2],sys.argv[3],sys.argv[4]
amount_native=float(sys.argv[5])
amount_usd=float(sys.argv[6])
reason=sys.argv[7]

decision_id=hashlib.sha256(
    f"{now()}|{chain}|{asset}|{dest}|{amount_native}|{amount_usd}|{reason}".encode()
).hexdigest()[:24]

row={
  "decision_id":decision_id,
  "created_at":now(),
  "source":"ceo_structured_decision",
  "action_type":"treasury_transfer",
  "chain":chain,
  "asset":asset,
  "destination":dest,
  "amount_native":amount_native,
  "amount_usd":amount_usd,
  "reason":reason,
  "status":"pending"
}

d=load()
d.setdefault("decisions",[]).append(row)
d["updated_at"]=now()
save(d)

print(json.dumps({
  "success":True,
  "status":"phase40_decision_queued",
  "decision":row
},indent=2))
