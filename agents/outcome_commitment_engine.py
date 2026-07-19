#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase24_bundle4_config.json"
VALIDATED=MEM/"validated_business_opportunities.json"
PROJECTS=MEM/"project_execution_registry.json"
OUT=MEM/"outcome_commitments.json"
STATE=MEM/"outcome_commitment_state.json"
HEALTH=MEM/"outcome_commitment_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def build():
    cfg=load(CFG,{})
    minimum=float(cfg.get("minimum_commitment_score",55))
    ops={x.get("id"):x for x in load(VALIDATED,{}).get("opportunities",[])}
    rows=[]
    for p in load(PROJECTS,{}).get("projects",[]):
        o=ops.get(p.get("source_opportunity_id"),{})
        score=float(o.get("validation_score",p.get("validation_score",0)) or 0)
        if score < minimum: continue
        rows.append({
          "project_id":p.get("project_id"),
          "title":p.get("title"),
          "commitment_score":score,
          "target_outcomes":[
            "Produce evidence-backed validation",
            "Reach a governed pilot-ready state",
            "Measure outcome quality and resource efficiency"
          ],
          "status":"internal_commitment_defined",
          "external_commitment_authorized":False,
          "created_at":now()
        })
    payload={"generated_at":now(),"commitment_count":len(rows),"commitments":rows}
    save(OUT,payload);save(STATE,{"last_built_at":now(),"commitment_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"commitment_count":len(rows)})
    return {"success":True,"status":"outcome_commitment_complete","report":payload}

r=build()
print(json.dumps(r,indent=2))
