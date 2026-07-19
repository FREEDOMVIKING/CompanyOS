#!/usr/bin/env python3
import json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"finance_forecast_bridge.json"; STATE=MEM/"finance_forecast_bridge_state.json"; HEALTH=MEM/"finance_forecast_bridge_health.json"
def now():return datetime.now(timezone.utc).isoformat()
def load(n,d):
    try:return json.loads((MEM/n).read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def run():
    forecast=load("business_forecast.json",{})
    accounting=load("accounting_state.json",{})
    priorities=load("customer_pipeline_priorities.json",{})
    payload={"generated_at":now(),"forecast":forecast,"accounting":accounting,
             "pipeline_priority_count":priorities.get("priority_count",0),
             "status":"internal_finance_forecast_context",
             "spending_authorized":False,"fund_transfer_authorized":False}
    save(OUT,payload);save(STATE,{"last_run_at":now()});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"finance_forecast_bridge_complete","report":payload}
r=run();print(json.dumps(r,indent=2))
