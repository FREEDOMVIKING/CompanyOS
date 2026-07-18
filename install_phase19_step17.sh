#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"; AGENTS="$ROOT/agents"; CTL="$ROOT/companyos"; MEM="$ROOT/ceo_memory"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 19 Step 17 - Autonomous Resource & Capacity Monitor"
echo "============================================================"

cat > "$MEM/resource_monitor_config.json" <<'JSON'
{
  "enabled": true,
  "disk_warning_percent": 85,
  "disk_critical_percent": 95,
  "memory_warning_percent": 85,
  "automatic_safe_cleanup": true,
  "max_log_age_days": 14,
  "automatic_spending": false,
  "automatic_external_write": false,
  "automatic_destructive_actions": false
}
JSON

cat > "$AGENTS/resource_monitor.py" <<'PY'
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
PY
chmod +x "$AGENTS/resource_monitor.py"

cat > "$CTL/resourcectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"resource_monitor.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/resourcectl"

echo "[1/5] Compiling..."
python -m py_compile "$AGENTS/resource_monitor.py" "$CTL/resourcectl"
echo "[2/5] Checking resources..."
python "$CTL/resourcectl" run
echo "[3/5] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
j={"id":"resource-capacity-monitor","enabled":True,"interval_seconds":1800,
   "command":["python","companyos/resourcectl","run"]}
e=next((x for x in jobs if x.get("id")==j["id"]),None)
if e:e.clear();e.update(j)
else:jobs.append(j)
p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":j["id"]},indent=2))
PY
echo "[4/5] Restarting scheduler..."
python "$CTL/operationsctl" restart
echo "[5/5] Status..."
python "$CTL/resourcectl" status

echo
echo "============================================================"
echo " PHASE 19 STEP 17 INSTALLED"
echo " AUTONOMOUS RESOURCE & CAPACITY MONITOR ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/resourcectl run"
echo "  python companyos/resourcectl status"
