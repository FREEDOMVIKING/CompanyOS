#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEMORY="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase18_step16_$(date +%Y%m%d_%H%M%S)"
cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEMORY" "$BACKUP"

echo "============================================================"
echo " Phase 18 Step 16 - Autonomous Governance & Approval Router"
echo "============================================================"

for f in "$AGENTS/governance_engine.py" "$CTL/governancectl" \
 "$MEMORY/governance_config.json" "$MEMORY/governance_state.json" \
 "$MEMORY/governance_queue.json" "$MEMORY/governance_health.json" \
 "$MEMORY/autonomous_operations_config.json"; do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEMORY/governance_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_internal_classification": true,
  "auto_approve_internal_read_only": true,
  "auto_approve_internal_reversible": true,
  "require_owner_approval_for_external_contact": true,
  "require_owner_approval_for_publication": true,
  "require_owner_approval_for_spending": true,
  "require_owner_approval_for_destructive_actions": true,
  "require_owner_approval_for_credentials_or_private_keys": true
}
JSON

cat > "$AGENTS/governance_engine.py" <<'PY'
#!/usr/bin/env python3
import json, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"
CFG=MEM/"governance_config.json"
QUEUE=MEM/"governance_queue.json"
STATE=MEM/"governance_state.json"
HEALTH=MEM/"governance_health.json"
ACTIONQ=MEM/"internal_action_queue.json"
DECISIONS=MEM/"ceo_decision_queue.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try: return json.loads(p.read_text())
    except Exception: return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(d,indent=2)); t.replace(p)

def classify():
    cfg=load(CFG,{})
    actions=load(ACTIONQ,{}).get("actions",[])
    decisions=load(DECISIONS,{}).get("decisions",[])
    routed=[]

    for a in actions:
        if a.get("status") != "pending": continue
        external=bool(a.get("external_action",False))
        routed.append({
            "source":"internal_action",
            "id":a.get("id"),
            "title":a.get("action"),
            "classification":"owner_approval_required" if external else "internal_auto_allowed",
            "reason":"External effect requires approval." if external else "Internal allowlisted action."
        })

    for d in decisions:
        if d.get("status") != "pending": continue
        routed.append({
            "source":"ceo_decision",
            "id":d.get("id"),
            "title":d.get("title"),
            "classification":"owner_review",
            "reason":"Pending CEO decision."
        })

    out={"generated_at":now(),"items":routed,"count":len(routed)}
    save(QUEUE,out)
    save(STATE,{
        "generated_at":now(),
        "total_items":len(routed),
        "internal_auto_allowed":sum(x["classification"]=="internal_auto_allowed" for x in routed),
        "owner_review_required":sum(x["classification"]!="internal_auto_allowed" for x in routed)
    })
    save(HEALTH,{"healthy":True,"last_run_at":now(),"item_count":len(routed)})
    return {"success":True,"status":"governance_routing_complete","queue":out}

def status():
    return {"success":True,"status":"governance_status","config":load(CFG,{}),
            "state":load(STATE,{}),"health":load(HEALTH,{})}

action=sys.argv[1] if len(sys.argv)>1 else "status"
result=classify() if action=="classify" else status() if action=="status" else {
    "success":False,"status":"unknown_action","allowed":["classify","status"]}
print(json.dumps(result,indent=2))
raise SystemExit(0 if result.get("success") else 1)
PY

chmod +x "$AGENTS/governance_engine.py"

cat > "$CTL/governancectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call(
 [sys.executable,str(r/"agents"/"governance_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/governancectl"

echo "[1/5] Compiling..."
python -m py_compile "$AGENTS/governance_engine.py" "$CTL/governancectl"

echo "[2/5] Running governance routing..."
python "$CTL/governancectl" classify

echo "[3/5] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text()); jobs=d.setdefault("jobs",[])
job={"id":"governance-router","enabled":True,"interval_seconds":900,
     "command":["python","companyos/governancectl","classify"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e: e.clear(); e.update(job)
else: jobs.append(job)
p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY

echo "[4/5] Restarting scheduler..."
python "$CTL/operationsctl" restart
python "$CTL/governancectl" status

echo "[5/5] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos"; errors=[]
req=[r/"agents"/"governance_engine.py",r/"companyos"/"governancectl",
r/"ceo_memory"/"governance_config.json",r/"ceo_memory"/"governance_state.json",
r/"ceo_memory"/"governance_queue.json",r/"ceo_memory"/"governance_health.json",
r/"ceo_memory"/"autonomous_operations_config.json"]
for p in req:
    if not p.exists() or p.stat().st_size<=0: errors.append(f"Missing/empty: {p}")
for p in req[:2]:
    try: py_compile.compile(str(p),doraise=True)
    except Exception as e: errors.append(str(e))
try:
    c=json.loads(req[2].read_text())
    for k in ["require_owner_approval_for_external_contact",
              "require_owner_approval_for_publication",
              "require_owner_approval_for_spending",
              "require_owner_approval_for_destructive_actions",
              "require_owner_approval_for_credentials_or_private_keys"]:
        if c.get(k) is not True: errors.append(f"{k} must be enabled")
    s=json.loads(req[6].read_text())
    j=next((x for x in s.get("jobs",[]) if x.get("id")=="governance-router"),None)
    if not j or j.get("enabled") is not True: errors.append("Governance scheduler job missing/disabled")
except Exception as e: errors.append(str(e))
print("--------------------------------------------")
print("Phase 18 Step 16 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors: print("ERROR:",e)
if errors: raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 18 STEP 16 INSTALLED"
echo " AUTONOMOUS GOVERNANCE & APPROVAL ROUTER ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/governancectl classify"
echo "  python companyos/governancectl status"
