#!/usr/bin/env python3
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory";SRC=MEM/"scored_opportunities.json";CFG=MEM/"phase25_bundle3_config.json";OUT=MEM/"strategic_execution_plans.json";STATE=MEM/"strategic_execution_state.json";HEALTH=MEM/"strategic_execution_health.json"
def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def hid(x):return hashlib.sha256(str(x).encode()).hexdigest()[:18]
def run():
    cfg=load(CFG,{});rows=[]
    for o in load(SRC,{}).get("opportunities",[]):
        if o.get("status")!="qualified_internal_candidate":continue
        if len(rows)>=int(cfg.get("maximum_active_plans",10)):break
        pid=hid(o.get("opportunity_id"))
        ms=[{"name":"evidence_validation","status":"planned","objective":"Validate assumptions and evidence"},{"name":"strategy_design","status":"planned","objective":"Design strongest internal strategy"},{"name":"execution_mapping","status":"planned","objective":"Map tasks dependencies and resources"},{"name":"risk_review","status":"planned","objective":"Review risks and failure modes"},{"name":"decision_ready","status":"planned","objective":"Prepare CEO-ready internal recommendation"}]
        rows.append({"plan_id":pid,"opportunity_id":o.get("opportunity_id"),"title":o.get("title"),"priority_score":o.get("score"),"milestones":ms,"status":"planned_internal","external_execution_authorized":False,"execution_boundary":"internal_non_destructive_only"})
    payload={"generated_at":now(),"plan_count":len(rows),"plans":rows}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"plan_count":len(rows)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"strategic_execution_planning_complete","report":payload}
print(json.dumps(run(),indent=2))
