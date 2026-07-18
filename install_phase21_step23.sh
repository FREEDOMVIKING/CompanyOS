#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"; AGENTS="$ROOT/agents"; CTL="$ROOT/companyos"; MEM="$ROOT/ceo_memory"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 21 Step 23 - Governed Decision Execution Planner"
echo "============================================================"

cat > "$MEM/governed_execution_plan_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_internal_planning": true,
  "maximum_plans_per_cycle": 10,
  "allowed_authority": ["internal_non_destructive_only"],
  "allowed_action_types": ["analyze", "research", "plan", "review", "prioritize", "coordinate"],
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

cat > "$AGENTS/governed_decision_execution_planner.py" <<'PY'
#!/usr/bin/env python3
import json,sys,re
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"governed_execution_plan_config.json"
DECISIONS=MEM/"governed_ceo_decisions.json"
STATE=MEM/"governed_execution_plan_state.json"
REPORT=MEM/"governed_execution_plan_report.json"
HEALTH=MEM/"governed_execution_plan_health.json"
OUT=MEM/"governed_internal_execution_plans.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def classify(text):
    s=str(text or "").lower()
    rules=[
      ("research",r"\bresearch\b|\binvestigat|\bmarket\b"),
      ("review",r"\breview\b|\baudit\b|\bcheck\b|\bvalidate\b"),
      ("prioritize",r"\bpriorit|\brank\b|\bscore\b"),
      ("coordinate",r"\bcoordinat|\bdelegat|\bassign\b"),
      ("plan",r"\bplan\b|\bstrateg|\broadmap\b"),
    ]
    for kind,pat in rules:
        if re.search(pat,s): return kind
    return "analyze"

def build():
    cfg=load(CFG,{})
    approved=load(DECISIONS,{}).get("approved",[])
    maximum=int(cfg.get("maximum_plans_per_cycle",10))
    allowed_auth=set(cfg.get("allowed_authority",[]))
    allowed_actions=set(cfg.get("allowed_action_types",[]))
    plans=[];held=[]

    for decision in approved[:maximum]:
        authority=decision.get("execution_authority")
        if authority not in allowed_auth:
            held.append({"decision_id":decision.get("decision_id"),"reason":"authority_not_allowed"})
            continue

        proposed=decision.get("proposed_internal_actions",[]) or []
        if not proposed:
            proposed=["Analyze the governed decision and prepare the next internal plan."]

        steps=[]
        for i,action in enumerate(proposed,1):
            action_type=classify(action)
            if action_type not in allowed_actions:
                continue
            steps.append({
              "step":i,"action_type":action_type,"instruction":str(action),
              "authority":"internal_non_destructive_only","status":"planned"
            })

        if not steps:
            held.append({"decision_id":decision.get("decision_id"),"reason":"no_allowed_internal_steps"})
            continue

        plans.append({
          "plan_id":f"{decision.get('decision_id')}-plan",
          "decision_id":decision.get("decision_id"),
          "opportunity_id":decision.get("opportunity_id"),
          "title":decision.get("title"),
          "recommended_direction":decision.get("recommended_direction"),
          "confidence":decision.get("confidence"),
          "execution_authority":"internal_non_destructive_only",
          "steps":steps,"status":"ready_for_internal_execution_queue",
          "created_at":now()
        })

    payload={"generated_at":now(),"plan_count":len(plans),"plans":plans,
      "note":"Plans contain internal non-destructive work only and grant no external authority."}
    save(OUT,payload)
    report={"generated_at":now(),"plan_count":len(plans),"held_count":len(held),
      "plans":plans,"held":held,
      "automatic_external_write":False,"automatic_customer_contact":False,"automatic_publication":False,
      "automatic_spending":False,"automatic_fund_transfer":False,"automatic_code_changes":False,
      "automatic_merge":False,"automatic_deploy":False,"automatic_destructive_actions":False}
    save(REPORT,report)
    save(STATE,{"last_planned_at":now(),"plan_count":len(plans),"held_count":len(held)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"plan_count":len(plans)})
    return {"success":True,"status":"governed_execution_planning_complete","report":report}

def status():
    return {"success":True,"status":"governed_execution_plan_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(REPORT,{}),"plans":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=build() if a=="plan" else status() if a=="status" else {"success":False,"allowed":["plan","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/governed_decision_execution_planner.py"

cat > "$CTL/governedplanctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"governed_decision_execution_planner.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/governedplanctl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/governed_decision_execution_planner.py" "$CTL/governedplanctl"
echo "[2/6] Building governed internal execution plans..."
python "$CTL/governedplanctl" plan
echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"governed-execution-planner","enabled":True,"interval_seconds":21600,
"command":["python","companyos/governedplanctl","plan"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2),encoding="utf-8")
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
echo "[4/6] Restarting scheduler..."
python "$CTL/operationsctl" restart
echo "[5/6] Checking status..."
python "$CTL/governedplanctl" status
echo "[6/6] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[r/"agents"/"governed_decision_execution_planner.py",r/"companyos"/"governedplanctl",
r/"ceo_memory"/"governed_execution_plan_config.json",r/"ceo_memory"/"governed_execution_plan_state.json",
r/"ceo_memory"/"governed_execution_plan_report.json",r/"ceo_memory"/"governed_execution_plan_health.json",
r/"ceo_memory"/"governed_internal_execution_plans.json",r/"ceo_memory"/"autonomous_operations_config.json"]
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
if not any(x.get("id")=="governed-execution-planner" and x.get("enabled") for x in sched.get("jobs",[])):
    errors.append("Scheduler job missing/disabled")
print("--------------------------------------------");print("Phase 21 Step 23 verification")
print(f"Errors: {len(errors)}");print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 21 STEP 23 INSTALLED"
echo " GOVERNED DECISION EXECUTION PLANNER ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/governedplanctl plan"
echo "  python companyos/governedplanctl status"
