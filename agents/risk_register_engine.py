#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
COLLAB=MEM/"specialist_collaboration_groups.json"
INCIDENTS=MEM/"incident_response_queue.json"
OUT=MEM/"enterprise_risk_register.json"
STATE=MEM/"risk_register_state.json"
HEALTH=MEM/"risk_register_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def rid(seed):return hashlib.sha256(str(seed).encode()).hexdigest()[:18]

def build():
    rows=[]
    for g in load(COLLAB,{}).get("groups",[]):
        for risk in g.get("combined_risks",[])[:20]:
            rows.append({
              "risk_id":rid(str(g.get("group_id"))+"|"+str(risk)),
              "source":"specialist_collaboration",
              "topic_id":g.get("topic_id"),
              "risk":risk,
              "severity":"medium",
              "status":"tracked"
            })
    for i in load(INCIDENTS,{}).get("incidents",[]):
        rows.append({
          "risk_id":rid(i.get("incident_id")),
          "source":"incident",
          "topic_id":i.get("component"),
          "risk":"Operational incident requires attention",
          "severity":i.get("severity","medium"),
          "status":"tracked"
        })
    payload={"generated_at":now(),"risk_count":len(rows),"risks":rows}
    save(OUT,payload);save(STATE,{"last_built_at":now(),"risk_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"risk_count":len(rows)})
    return {"success":True,"status":"risk_register_complete","register":payload}

r=build()
print(json.dumps(r,indent=2))
