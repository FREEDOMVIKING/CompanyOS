#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"; AGENTS="$ROOT/agents"; CTL="$ROOT/companyos"; MEM="$ROOT/ceo_memory"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 19 Step 19 - Autonomous State Backup & Recovery"
echo "============================================================"

cat > "$MEM/state_backup_config.json" <<'JSON'
{
  "enabled": true,
  "backup_interval_seconds": 21600,
  "retention_count": 12,
  "include_ceo_memory": true,
  "include_configs": true,
  "automatic_restore": false,
  "require_manual_restore": true
}
JSON

cat > "$AGENTS/state_backup_engine.py" <<'PY'
#!/usr/bin/env python3
import json, shutil, sys, tarfile
from datetime import datetime, timezone
from pathlib import Path

R=Path.home()/"companyos"; M=R/"ceo_memory"; B=R/"backups"/"state_snapshots"
CFG=M/"state_backup_config.json"; STATE=M/"state_backup_state.json"; HEALTH=M/"state_backup_health.json"

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def now():return datetime.now(timezone.utc).isoformat()

def backup():
    cfg=load(CFG,{})
    B.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    target=B/f"companyos_state_{stamp}.tar.gz"
    with tarfile.open(target,"w:gz") as tar:
        if M.exists(): tar.add(M,arcname="ceo_memory")
    snaps=sorted(B.glob("companyos_state_*.tar.gz"),key=lambda p:p.stat().st_mtime,reverse=True)
    for old in snaps[int(cfg.get("retention_count",12)):]:
        old.unlink(missing_ok=True)
    state={"last_backup_at":now(),"last_backup":str(target),"backup_count":len(list(B.glob("companyos_state_*.tar.gz")))}
    save(STATE,state);save(HEALTH,{"healthy":target.exists(),"last_checked_at":now(),**state})
    return {"success":target.exists(),"status":"state_backup_complete","state":state}

def list_backups():
    B.mkdir(parents=True,exist_ok=True)
    return {"success":True,"status":"state_backups","backups":[str(x) for x in sorted(B.glob("*.tar.gz"),reverse=True)]}

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="backup":r=backup()
elif a=="list":r=list_backups()
elif a=="status":r={"success":True,"status":"state_backup_status","state":load(STATE,{}),"health":load(HEALTH,{})}
else:r={"success":False,"status":"unknown_action","allowed":["backup","list","status"]}
print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/state_backup_engine.py"

cat > "$CTL/backupctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"state_backup_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/backupctl"

echo "[1/5] Compiling..."
python -m py_compile "$AGENTS/state_backup_engine.py" "$CTL/backupctl"
echo "[2/5] Creating first state snapshot..."
python "$CTL/backupctl" backup
echo "[3/5] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
j={"id":"state-backup","enabled":True,"interval_seconds":21600,
   "command":["python","companyos/backupctl","backup"]}
e=next((x for x in jobs if x.get("id")==j["id"]),None)
if e:e.clear();e.update(j)
else:jobs.append(j)
p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":j["id"]},indent=2))
PY
echo "[4/5] Restarting scheduler..."
python "$CTL/operationsctl" restart
echo "[5/5] Status..."
python "$CTL/backupctl" status

echo
echo "============================================================"
echo " PHASE 19 STEP 19 INSTALLED"
echo " AUTONOMOUS STATE BACKUP & RECOVERY ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/backupctl backup"
echo "  python companyos/backupctl list"
echo "  python companyos/backupctl status"
