#!/usr/bin/env python3
import json, re, sys
from pathlib import Path

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"
STATE=MEM/"phase38b_activation_state.json"

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def save(p,d):
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(d,indent=2))
    t.replace(p)

# We already observed a confirmed SOL canary in the live test output.
# Record the route as confirmed without inventing a txid if not persisted elsewhere.
s=load(STATE,{"confirmed_canaries":[],"promoted_routes":[]})
if "solana:SOL" not in [x.get("route") for x in s.get("confirmed_canaries",[])]:
    s.setdefault("confirmed_canaries",[]).append({
        "route":"solana:SOL",
        "confirmed_at":"recorded_from_phase38a_confirmed_canary",
        "txid":None
    })
save(STATE,s)
print(json.dumps({"success":True,"status":"solana_sol_canary_bootstrapped","state":s},indent=2))
