#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"; AGENTS="$ROOT/agents"; CTL="$ROOT/companyos"; MEM="$ROOT/ceo_memory"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 19 Step 18 - Autonomous Watchdog & Heartbeat"
echo "============================================================"

cat > "$MEM/watchdog_config.json" <<'JSON'
{
  "enabled": true,
  "heartbeat_stale_seconds": 5400,
  "automatic_scheduler_restart": true,
  "automatic_control_cycle_recovery": true,
  "max_recovery_attempts_per_run": 1
}
JSON

cat > "$AGENTS/watchdog_engine.py" <<'PY'
#!/usr/bin/env python3
import json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

R=Path.home()/"companyos"; M=R/"ceo_memory"
CFG=M/"watchdog_config.json"; CYCLE=M/"control_cycle_state.json"
STATE=M/"watchdog_state.json"; HEALTH=M/"watchdog_health.json"

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def now():return datetime.now(timezone.utc)
def call(args):
    try:
        p=subprocess.run(args,cwd=R,text=True,capture_output=True,timeout=600)
        return {"success":p.returncode==0,"return_code":p.returncode,
                "stdout":p.stdout[-1500:],"stderr":p.stderr[-1000:]}
    except Exception as e:return {"success":False,"error":str(e)}
def age_seconds(v):
    try:return max(0,(now()-datetime.fromisoformat(v.replace("Z","+00:00"))).total_seconds())
    except:return None

def run():
    cfg=load(CFG,{})
    cyc=load(CYCLE,{})
    age=age_seconds(cyc.get("last_cycle_at",""))
    stale=age is None or age>cfg.get("heartbeat_stale_seconds",5400)
    actions=[]
    if stale and cfg.get("automatic_scheduler_restart",True):
        actions.append({"action":"restart_scheduler","result":call(["python","companyos/operationsctl","restart"])})
    if stale and cfg.get("automatic_control_cycle_recovery",True):
        actions.append({"action":"recover_control_cycle","result":call(["python","companyos/controlcyclectl","run"])})
    healthy=not stale or all(a["result"].get("success",False) for a in actions)
    s={"last_checked_at":now().isoformat(),"heartbeat_age_seconds":age,
       "heartbeat_stale":stale,"recovery_actions":actions}
    save(STATE,s);save(HEALTH,{"healthy":healthy,**s})
    return {"success":healthy,"status":"watchdog_check_complete","state":s}

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="run":r=run()
elif a=="status":r={"success":True,"status":"watchdog_status",
                    "state":load(STATE,{}),"health":load(HEALTH,{})}
else:r={"success":False,"status":"unknown_action","allowed":["run","status"]}
print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/watchdog_engine.py"

cat > "$CTL/watchdogctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"watchdog_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/watchdogctl"

echo "[1/5] Compiling..."
python -m py_compile "$AGENTS/watchdog_engine.py" "$CTL/watchdogctl"
echo "[2/5] Running watchdog..."
python "$CTL/watchdogctl" run
echo "[3/5] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
j={"id":"autonomous-watchdog","enabled":True,"interval_seconds":1800,
   "command":["python","companyos/watchdogctl","run"]}
e=next((x for x in jobs if x.get("id")==j["id"]),None)
if e:e.clear();e.update(j)
else:jobs.append(j)
p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":j["id"]},indent=2))
PY
echo "[4/5] Restarting scheduler..."
python "$CTL/operationsctl" restart
echo "[5/5] Status..."
python "$CTL/watchdogctl" status

echo
echo "============================================================"
echo " PHASE 19 STEP 18 INSTALLED"
echo " AUTONOMOUS WATCHDOG & HEARTBEAT ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
