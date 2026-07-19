#!/usr/bin/env python3
from __future__ import annotations
import json,sys,os
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"connector_readiness_report.json"
STATE=MEM/"connector_readiness_state.json"
HEALTH=MEM/"connector_readiness_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def check():
    checks=[
      {"connector":"openrouter","configured":bool(os.getenv("OPENROUTER_API_KEY","").strip()),
       "capability":"ai_reasoning","external_side_effects":False},
      {"connector":"github","configured":(ROOT/".git").exists(),
       "capability":"source_control","external_side_effects":True},
      {"connector":"crm","configured":(MEM/"crm_state.json").exists(),
       "capability":"customer_records","external_side_effects":False},
      {"connector":"accounting","configured":(MEM/"accounting_state.json").exists(),
       "capability":"finance_records","external_side_effects":False}
    ]
    payload={"generated_at":now(),"connector_count":len(checks),"connectors":checks}
    save(OUT,payload);save(STATE,{"last_checked_at":now(),"connector_count":len(checks)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"connector_count":len(checks)})
    return {"success":True,"status":"connector_readiness_complete","report":payload}

r=check()
print(json.dumps(r,indent=2))
