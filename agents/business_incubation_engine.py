#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase24_bundle2_config.json"
PROJECTS=MEM/"project_execution_registry.json"
OUT=MEM/"business_incubation_portfolio.json"
STATE=MEM/"business_incubation_state.json"
HEALTH=MEM/"business_incubation_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def incubate():
    cfg=load(CFG,{})
    projects=load(PROJECTS,{}).get("projects",[])
    rows=[]
    for p in projects[:int(cfg.get("maximum_incubation_candidates",10))]:
        rows.append({
          "project_id":p.get("project_id"),
          "title":p.get("title"),
          "incubation_stage":"concept_validation",
          "validation_score":p.get("validation_score"),
          "hypothesis":"This project may create measurable business value if evidence, execution readiness, and outcomes remain favorable.",
          "next_internal_steps":[
            "Validate customer or market need with available evidence",
            "Define measurable success criteria",
            "Estimate internal effort and dependencies",
            "Prepare a governed pilot plan"
          ],
          "status":"incubating_internal_only",
          "external_launch_authorized":False
        })
    payload={"generated_at":now(),"candidate_count":len(rows),"candidates":rows}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"candidate_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"candidate_count":len(rows)})
    return {"success":True,"status":"business_incubation_complete","portfolio":payload}

def status():
    return {"success":True,"status":"business_incubation_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"portfolio":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=incubate() if a=="incubate" else status() if a=="status" else {"success":False,"allowed":["incubate","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
