#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
DELIVERY=MEM/"delivery_pipeline.json"
COMMIT=MEM/"outcome_commitments.json"
OUT=MEM/"executive_review_queue.json"
STATE=MEM/"executive_review_state.json"
HEALTH=MEM/"executive_review_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def build():
    commitments={x.get("project_id"):x for x in load(COMMIT,{}).get("commitments",[])}
    rows=[]
    for d in load(DELIVERY,{}).get("deliveries",[]):
        c=commitments.get(d.get("project_id"),{})
        rows.append({
          "project_id":d.get("project_id"),
          "title":d.get("title"),
          "delivery_status":d.get("status"),
          "commitment_score":c.get("commitment_score"),
          "review_status":"ready_for_internal_executive_review",
          "external_authority_granted":False
        })
    payload={"generated_at":now(),"review_count":len(rows),"reviews":rows}
    save(OUT,payload);save(STATE,{"last_built_at":now(),"review_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"review_count":len(rows)})
    return {"success":True,"status":"executive_review_complete","queue":payload}

r=build()
print(json.dumps(r,indent=2))
