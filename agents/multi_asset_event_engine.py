#!/usr/bin/env python3
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
BAL=MEM/"multi_asset_treasury_balances.json"
SNAP=MEM/"multi_asset_balance_snapshot.json"
EVENTS=MEM/"multi_asset_treasury_events.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):p.write_text(json.dumps(d,indent=2))
def eid(s):return hashlib.sha256(s.encode()).hexdigest()[:20]

cur=load(BAL,{}).get("balances",[])
prev={x.get("wallet_id"):x for x in load(SNAP,{}).get("balances",[])}
events=load(EVENTS,{"events":[]})
for w in cur:
    p=prev.get(w.get("wallet_id"),{})
    for asset,bal in (w.get("assets") or {}).items():
        if bal is None:continue
        old=(p.get("assets") or {}).get(asset)
        if old is None:continue
        delta=float(bal)-float(old)
        if abs(delta)>0:
            events["events"].append({
              "event_id":eid(f"{w['wallet_id']}|{asset}|{now()}|{delta}"),
              "wallet_id":w["wallet_id"],"chain":w["chain"],"asset":asset,
              "balance_delta":delta,"direction":"incoming" if delta>0 else "outgoing",
              "detected_at":now()
            })
events["events"]=events["events"][-10000:];events["updated_at"]=now()
save(EVENTS,events);save(SNAP,{"generated_at":now(),"balances":cur})
print(json.dumps({"success":True,"status":"multi_asset_event_generation_complete","event_count":len(events["events"])},indent=2))
