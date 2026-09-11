#!/usr/bin/env python3
import json, shutil, sys, time
from datetime import datetime, timezone
from pathlib import Path

R=Path.home()/"companyos"; M=R/"ceo_memory"; LOG=R/"logs"
CFG=M/"resource_monitor_config.json"; REPORT=M/"resource_monitor_report.json"; HEALTH=M/"resource_monitor_health.json"

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def now():return datetime.now(timezone.utc).isoformat()
def mem():
    vals={}
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            k,v=line.split(":",1); vals[k]=int(v.strip().split()[0])
        total=vals.get("MemTotal",0); avail=vals.get("MemAvailable",0)
        return round((total-avail)*100/total,2) if total else 0
    except:return 0
def cleanup(days):
    removed=0; cutoff=time.time()-days*86400
    if LOG.exists():
        for p in LOG.glob("*.log.*"):
            try:
                if p.stat().st_mtime<cutoff:p.unlink();removed+=1
            except:pass
    return removed

def run():
    cfg=load(CFG,{})
    d=shutil.disk_usage(R); disk=round(d.used*100/d.total,2); memory=mem()
    level="healthy"
    if disk>=cfg.get("disk_critical_percent",95): level="critical"
    elif disk>=cfg.get("disk_warning_percent",85) or memory>=cfg.get("memory_warning_percent",85): level="warning"
    removed=cleanup(cfg.get("max_log_age_days",14)) if cfg.get("automatic_safe_cleanup",True) else 0
    rep={"generated_at":now(),"status":level,"disk_used_percent":disk,
         "memory_used_percent":memory,"free_disk_bytes":d.free,
         "safe_cleanup_files_removed":removed,
         "automatic_spending":False,"automatic_external_write":False,
         "automatic_destructive_actions":False}
    save(REPORT,rep);save(HEALTH,{"healthy":level!="critical","last_checked_at":now(),"status":level})
    return {"success":True,"status":"resource_check_complete","report":rep}

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="run":r=run()
elif a=="status":r={"success":True,"status":"resource_monitor_status","health":load(HEALTH,{}),"report":load(REPORT,{})}
else:r={"success":False,"status":"unknown_action","allowed":["run","status"]}
print(json.dumps(r,indent=2))
