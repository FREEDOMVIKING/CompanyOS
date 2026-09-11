#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"; AGENTS="$ROOT/agents"; CTL="$ROOT/companyos"; MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase19_step9_$(date +%Y%m%d_%H%M%S)"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " Phase 19 Step 9 - Autonomous Preflight Gate"
echo "============================================================"

cat > "$MEM/preflight_gate_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_preflight": true,
  "max_automatic_risk_score": 34,
  "require_clean_worktree_for_deploy": true,
  "require_github_health": true,
  "automatic_merge": false,
  "automatic_deploy": false,
  "automatic_spending": false
}
JSON

cat > "$AGENTS/preflight_gate.py" <<'PY'
#!/usr/bin/env python3
import json,sys
from datetime import datetime,timezone
from pathlib import Path

R=Path.home()/"companyos"; M=R/"ceo_memory"
CFG=M/"preflight_gate_config.json"; CHANGE=M/"github_change_report.json"
GH=M/"github_read_health.json"; OUT=M/"preflight_gate_report.json"; HEALTH=M/"preflight_gate_health.json"

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):p.write_text(json.dumps(d,indent=2))
def run():
    c=load(CFG,{}); ch=load(CHANGE,{}); gh=load(GH,{})
    risk=int(ch.get("risk_score",100)); blockers=[]
    if risk>int(c.get("max_automatic_risk_score",34)): blockers.append("risk_score_above_automatic_threshold")
    if c.get("require_clean_worktree_for_deploy") and ch.get("changed_files"): blockers.append("working_tree_has_changes")
    if c.get("require_github_health") and not gh.get("healthy",False): blockers.append("github_connector_unhealthy")
    decision="ready_for_review" if not blockers else "blocked"
    out={"generated_at":datetime.now(timezone.utc).isoformat(),"decision":decision,
         "risk_score":risk,"blockers":blockers,
         "automatic_merge":False,"automatic_deploy":False,"automatic_spending":False}
    save(OUT,out);save(HEALTH,{"healthy":True,"last_checked_at":out["generated_at"],"decision":decision})
    return {"success":True,"status":"preflight_complete","report":out}
a=sys.argv[1] if len(sys.argv)>1 else "run"
r=run() if a=="run" else {"success":True,"status":"preflight_status","report":load(OUT,{})}
print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/preflight_gate.py"

cat > "$CTL/preflightctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"preflight_gate.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/preflightctl"

echo "[1/5] Compiling..."
python -m py_compile "$AGENTS/preflight_gate.py" "$CTL/preflightctl"
echo "[2/5] Running preflight..."
python "$CTL/preflightctl" run
echo "[3/5] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
j={"id":"autonomous-preflight","enabled":True,"interval_seconds":1800,
"command":["python","companyos/preflightctl","run"]}
e=next((x for x in jobs if x.get("id")==j["id"]),None)
if e:e.clear();e.update(j)
else:jobs.append(j)
p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":j["id"]},indent=2))
PY
echo "[4/5] Restarting scheduler..."
python "$CTL/operationsctl" restart
echo "[5/5] Verifying..."
python "$CTL/preflightctl" status

echo
echo "============================================================"
echo " PHASE 19 STEP 9 INSTALLED"
echo " AUTONOMOUS PREFLIGHT GATE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/preflightctl run"
echo "  python companyos/preflightctl status"
