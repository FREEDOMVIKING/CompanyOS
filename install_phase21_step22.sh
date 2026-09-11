#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"; AGENTS="$ROOT/agents"; CTL="$ROOT/companyos"; MEM="$ROOT/ceo_memory"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 21 Step 22 - CEO Decision Governance Gate"
echo "============================================================"

cat > "$MEM/ceo_decision_governance_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_internal_governance": true,
  "maximum_decisions_per_cycle": 10,
  "minimum_confidence": 0.5,
  "allowed_automatic_classes": ["internal_candidate"],
  "automatic_external_write": false,
  "automatic_customer_contact": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_fund_transfer": false,
  "automatic_code_changes": false,
  "automatic_merge": false,
  "automatic_deploy": false,
  "automatic_destructive_actions": false
}
JSON

cat > "$AGENTS/ceo_decision_governance_gate.py" <<'PY'
#!/usr/bin/env python3
import json,sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"ceo_decision_governance_config.json"
DECISIONS=MEM/"ceo_decision_candidates.json"
STATE=MEM/"ceo_decision_governance_state.json"
REPORT=MEM/"ceo_decision_governance_report.json"
HEALTH=MEM/"ceo_decision_governance_health.json"
OUT=MEM/"governed_ceo_decisions.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def num(v,d=0):
    try:return float(v)
    except:return float(d)

def govern():
    cfg=load(CFG,{})
    rows=load(DECISIONS,{}).get("decisions",[])
    maximum=int(cfg.get("maximum_decisions_per_cycle",10))
    minimum=num(cfg.get("minimum_confidence",.5))
    allowed=set(cfg.get("allowed_automatic_classes",["internal_candidate"]))
    approved=[];held=[]

    for row in rows[:maximum]:
        reasons=[]
        if num(row.get("confidence",0))<minimum: reasons.append("confidence_below_threshold")
        if row.get("decision_class") not in allowed: reasons.append("decision_class_not_automatic")
        if reasons:
            held.append({**row,"governance_status":"held","hold_reasons":reasons})
        else:
            approved.append({**row,"governance_status":"approved_internal_only",
              "execution_authority":"internal_non_destructive_only","governed_at":now()})

    payload={"generated_at":now(),"approved_count":len(approved),"held_count":len(held),
      "approved":approved,"held":held,
      "note":"Governance approval does not grant external, financial, deployment, publication, or destructive authority."}
    save(OUT,payload)
    report={"generated_at":now(),"approved_count":len(approved),"held_count":len(held),
      "approved":approved,"held":held,
      "automatic_external_write":False,"automatic_customer_contact":False,"automatic_publication":False,
      "automatic_spending":False,"automatic_fund_transfer":False,"automatic_code_changes":False,
      "automatic_merge":False,"automatic_deploy":False,"automatic_destructive_actions":False}
    save(REPORT,report);save(STATE,{"last_governed_at":now(),"approved_count":len(approved),"held_count":len(held)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"approved_count":len(approved)})
    return {"success":True,"status":"ceo_decision_governance_complete","report":report}

def status():
    return {"success":True,"status":"ceo_decision_governance_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(REPORT,{}),"decisions":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=govern() if a=="govern" else status() if a=="status" else {"success":False,"allowed":["govern","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/ceo_decision_governance_gate.py"

cat > "$CTL/ceodecisiongovernctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"ceo_decision_governance_gate.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/ceodecisiongovernctl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/ceo_decision_governance_gate.py" "$CTL/ceodecisiongovernctl"
echo "[2/6] Governing CEO decision candidates..."
python "$CTL/ceodecisiongovernctl" govern
echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"ceo-decision-governance","enabled":True,"interval_seconds":21600,
"command":["python","companyos/ceodecisiongovernctl","govern"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2),encoding="utf-8")
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
echo "[4/6] Restarting scheduler..."
python "$CTL/operationsctl" restart
echo "[5/6] Checking status..."
python "$CTL/ceodecisiongovernctl" status
echo "[6/6] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[r/"agents"/"ceo_decision_governance_gate.py",r/"companyos"/"ceodecisiongovernctl",
r/"ceo_memory"/"ceo_decision_governance_config.json",r/"ceo_memory"/"ceo_decision_governance_state.json",
r/"ceo_memory"/"ceo_decision_governance_report.json",r/"ceo_memory"/"ceo_decision_governance_health.json",
r/"ceo_memory"/"governed_ceo_decisions.json",r/"ceo_memory"/"autonomous_operations_config.json"]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:2]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
cfg=json.loads(req[2].read_text())
for k in ["automatic_external_write","automatic_customer_contact","automatic_publication","automatic_spending",
"automatic_fund_transfer","automatic_code_changes","automatic_merge","automatic_deploy","automatic_destructive_actions"]:
    if cfg.get(k) is not False:errors.append(f"{k} must remain disabled")
sched=json.loads(req[7].read_text())
if not any(x.get("id")=="ceo-decision-governance" and x.get("enabled") for x in sched.get("jobs",[])):
    errors.append("Scheduler job missing/disabled")
print("--------------------------------------------");print("Phase 21 Step 22 verification")
print(f"Errors: {len(errors)}");print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 21 STEP 22 INSTALLED"
echo " CEO DECISION GOVERNANCE GATE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/ceodecisiongovernctl govern"
echo "  python companyos/ceodecisiongovernctl status"
