#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OBS=MEM/"operations_observability_report.json"
OUT=MEM/"incident_response_queue.json"
STATE=MEM/"incident_response_state.json"
HEALTH=MEM/"incident_response_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def iid(seed):return hashlib.sha256(str(seed).encode()).hexdigest()[:18]

def triage():
    obs=load(OBS,{})
    rows=[]
    for comp in obs.get("unhealthy_components",[]):
        rows.append({
          "incident_id":iid(comp),
          "component":comp,
          "severity":"medium",
          "status":"triage_internal",
          "recommended_actions":[
            "Inspect current health and state files",
            "Re-run the failing internal component",
            "Re-run dependency chain if needed",
            "Escalate for human review before any external or destructive action"
          ],
          "external_action_authorized":False,
          "created_at":now()
        })
    payload={"generated_at":now(),"incident_count":len(rows),"incidents":rows}
    save(OUT,payload);save(STATE,{"last_triaged_at":now(),"incident_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"incident_count":len(rows)})
    return {"success":True,"status":"incident_triage_complete","queue":payload}

r=triage()
print(json.dumps(r,indent=2))
