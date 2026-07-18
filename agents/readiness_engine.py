#!/usr/bin/env python3
import json, sys
from datetime import datetime, timezone
from pathlib import Path

R=Path.home()/"companyos"; M=R/"ceo_memory"; C=R/"companyos"
CFG=M/"readiness_config.json"; STATE=M/"readiness_state.json"
REPORT=M/"readiness_report.json"; HEALTH=M/"readiness_health.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def check():
    cfg=load(CFG,{})
    required=cfg.get("required_controllers",[])
    controllers=[]
    missing=[]
    for name in required:
        p=C/name
        ok=p.exists() and p.stat().st_size>0
        controllers.append({"name":name,"ready":ok})
        if not ok: missing.append(name)

    health_files=list(M.glob("*_health.json"))
    healthy=0; unhealthy=[]; unreadable=[]
    for p in health_files:
        try:
            d=json.loads(p.read_text())
            if d.get("healthy") is False: unhealthy.append(p.name)
            else: healthy+=1
        except Exception:
            unreadable.append(p.name)

    scheduler=M/"autonomous_operations_config.json"
    scheduler_ok=False; enabled_jobs=0
    try:
        d=json.loads(scheduler.read_text())
        jobs=d.get("jobs",[])
        enabled_jobs=sum(1 for x in jobs if x.get("enabled") is True)
        scheduler_ok=enabled_jobs>0
    except Exception: pass

    total_checks=len(required)+1+len(health_files)
    passed=(len(required)-len(missing))+(1 if scheduler_ok else 0)+healthy
    score=round(100*passed/max(1,total_checks),2)

    issues=[]
    if missing: issues.append({"type":"missing_controllers","items":missing})
    if unhealthy: issues.append({"type":"unhealthy_components","items":unhealthy})
    if unreadable: issues.append({"type":"unreadable_health_files","items":unreadable})
    if not scheduler_ok: issues.append({"type":"scheduler_not_ready"})

    report={"generated_at":now(),"readiness_score":score,
            "controllers":controllers,"enabled_scheduler_jobs":enabled_jobs,
            "health_files_checked":len(health_files),"issues":issues,
            "ready":not missing and scheduler_ok and not unhealthy and not unreadable}
    save(REPORT,report)
    old=load(STATE,{})
    save(STATE,{"generated_at":now(),"cycle_count":int(old.get("cycle_count",0))+1,
                "readiness_score":score,"issue_count":len(issues),
                "ready":report["ready"]})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),
                 "system_ready":report["ready"],"readiness_score":score,
                 "issue_count":len(issues)})
    return {"success":True,"status":"readiness_check_complete","report":report}

def status():
    return {"success":True,"status":"readiness_status",
            "state":load(STATE,{}),"health":load(HEALTH,{}),"report":load(REPORT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=check() if a=="check" else status() if a=="status" else {
 "success":False,"status":"unknown_action","allowed":["check","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
