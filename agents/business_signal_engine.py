#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"business_signals.json"; STATE=MEM/"business_signal_state.json"; HEALTH=MEM/"business_signal_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(name,d):
    p=MEM/name
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def run():
    signals=[]
    forecast=load("business_forecast.json",{})
    priorities=load("portfolio_resource_priorities.json",{})
    outcomes=load("outcome_tracker_report.json",{})
    crm=load("crm_state.json",{})
    accounting=load("accounting_state.json",{})

    if forecast:
        signals.append({"type":"forecast","strength":70,"source":"business_forecast","data":forecast})
    for x in priorities.get("candidates",[])[:10]:
        signals.append({"type":"priority_opportunity","strength":float(x.get("resource_readiness_score",50) or 50),"source":"portfolio","data":x})
    if outcomes:
        signals.append({"type":"outcomes","strength":60,"source":"outcome_tracker","data":outcomes})
    if crm:
        signals.append({"type":"crm","strength":55,"source":"crm","data":crm})
    if accounting:
        signals.append({"type":"finance","strength":65,"source":"accounting","data":accounting})

    payload={"generated_at":now(),"signal_count":len(signals),"signals":signals}
    save(OUT,payload); save(STATE,{"last_run_at":now(),"signal_count":len(signals)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"signal_count":len(signals)})
    return {"success":True,"status":"business_signal_generation_complete","report":payload}

def status():
    return {"success":True,"status":"business_signal_status","state":load("business_signal_state.json",{}),
      "health":load("business_signal_health.json",{}),"report":load("business_signals.json",{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=run() if a=="run" else status() if a=="status" else {"success":False,"allowed":["run","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
