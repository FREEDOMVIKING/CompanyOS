#!/usr/bin/env python3
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"proposal_draft_queue.json"; STATE=MEM/"proposal_draft_state.json"; HEALTH=MEM/"proposal_draft_health.json"
def now():return datetime.now(timezone.utc).isoformat()
def load(n,d):
    try:return json.loads((MEM/n).read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def did(x):return hashlib.sha256(str(x).encode()).hexdigest()[:16]
def run():
    rows=[]
    for x in load("customer_pipeline_priorities.json",{}).get("priorities",[])[:20]:
        title=x.get("title","Opportunity")
        rows.append({"draft_id":did(x.get("priority_id")),"title":f"Draft proposal: {title}",
          "source_priority_id":x.get("priority_id"),
          "outline":["Problem / opportunity","Proposed scope","Expected outcomes","Assumptions","Next-step questions"],
          "status":"draft_internal_review_only","send_authorized":False,"created_at":now()})
    payload={"generated_at":now(),"draft_count":len(rows),"drafts":rows}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"draft_count":len(rows)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"proposal_draft_generation_complete","queue":payload}
def status():return {"success":True,"status":"proposal_draft_status","state":load("proposal_draft_state.json",{}),"health":load("proposal_draft_health.json",{})}
a=sys.argv[1] if len(sys.argv)>1 else "status";r=run() if a=="run" else status();print(json.dumps(r,indent=2))
