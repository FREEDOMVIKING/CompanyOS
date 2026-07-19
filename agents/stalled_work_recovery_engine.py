#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory";CFG=MEM/"phase25_bundle3_config.json";OUT=MEM/"stalled_work_recovery_plan.json";STATE=MEM/"stalled_work_recovery_state.json";HEALTH=MEM/"stalled_work_recovery_health.json"
FILES=[MEM/"specialist_runtime_report.json",MEM/"phase25_bundle1_report.json",MEM/"phase25_bundle2_report.json"]
def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def run():
    cfg=load(CFG,{});actions=[]
    for p in FILES:
        d=load(p,{});fails=d.get("failed_steps",[])
        if not fails and isinstance(d.get("report"),dict):fails=d["report"].get("failed_steps",[])
        for f in fails:actions.append({"source":p.name,"failed_step":f,"recommended_action":"retry_internal_after_prerequisite_refresh","max_attempts":cfg.get("maximum_recovery_attempts",3),"status":"recovery_planned","external_action_authorized":False})
    payload={"generated_at":now(),"recovery_action_count":len(actions),"actions":actions}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"recovery_action_count":len(actions)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"stalled_work_recovery_complete","report":payload}
print(json.dumps(run(),indent=2))
