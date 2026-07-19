#!/usr/bin/env python3
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
BAL=MEM/"live_treasury_balances.json"
SNAP=MEM/"treasury_balance_snapshot.json"
EVENTS=MEM/"treasury_events.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):p.write_text(json.dumps(d,indent=2))
def eid(s):return hashlib.sha256(s.encode()).hexdigest()[:20]

current=load(BAL,{}).get("balances",[])
previous={x.get("wallet_id"):x for x in load(SNAP,{}).get("balances",[])}
events=load(EVENTS,{"events":[]})
for x in current:
    if x.get("status")!="ok" or x.get("balance") is None: continue
    p=previous.get(x.get("wallet_id"))
    if not p or p.get("balance") is None: continue
    delta=float(x["balance"])-float(p["balance"])
    if abs(delta)>0:
        ev={
          "event_id":eid(f"{x['wallet_id']}|{now()}|{delta}"),
          "wallet_id":x["wallet_id"],
          "chain":x["chain"],
          "asset":x.get("native_asset"),
          "balance_delta":delta,
          "direction":"incoming" if delta>0 else "outgoing",
          "detected_at":now()
        }
        events["events"].append(ev)
events["events"]=events["events"][-5000:]
events["updated_at"]=now()
save(EVENTS,events);save(SNAP,{"generated_at":now(),"balances":current})
print(json.dumps({"success":True,"status":"treasury_event_generation_complete","event_count":len(events["events"])},indent=2))
