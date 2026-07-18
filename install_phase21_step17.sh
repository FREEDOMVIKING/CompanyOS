#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"; AGENTS="$ROOT/agents"; CTL="$ROOT/companyos"; MEM="$ROOT/ceo_memory"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 21 Step 17 - Specialist Delegation Planner"
echo "============================================================"

cat > "$MEM/specialist_delegation_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_internal_delegation_planning": true,
  "maximum_assignments": 10,
  "specialists": {
    "research": "research_agent",
    "strategy": "strategy_agent",
    "product": "product_agent",
    "engineering": "engineering_agent",
    "operations": "operations_agent",
    "marketing": "marketing_agent",
    "finance": "finance_analysis_agent"
  },
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

cat > "$AGENTS/specialist_delegation_planner.py" <<'PY'
#!/usr/bin/env python3
import json,sys,re
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"specialist_delegation_config.json"
PLAN=MEM/"internal_resource_plan.json"
STATE=MEM/"specialist_delegation_state.json"
REPORT=MEM/"specialist_delegation_report.json"
HEALTH=MEM/"specialist_delegation_health.json"
OUT=MEM/"specialist_assignment_plan.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def choose(title,category):
    text=f"{title} {category}".lower()
    rules=[
      ("research",r"research|market|discover|analysis|investigat"),
      ("marketing",r"market|growth|audience|brand|content|lead"),
      ("finance",r"finance|revenue|pricing|margin|capital|cost"),
      ("engineering",r"software|code|app|api|platform|automation|technical"),
      ("product",r"product|customer|feature|offer"),
      ("operations",r"operation|process|workflow|service"),
    ]
    for role,pat in rules:
        if re.search(pat,text):return role
    return "strategy"

def delegate():
    cfg=load(CFG,{})
    allocations=load(PLAN,{}).get("allocations",[])
    specialists=cfg.get("specialists",{})
    maximum=int(cfg.get("maximum_assignments",10))
    assignments=[]
    for row in allocations[:maximum]:
        role=choose(row.get("title",""),row.get("category",""))
        assignments.append({
          "assignment_id":f"{row.get('id') or 'opportunity'}-{role}",
          "opportunity_id":row.get("id"),"title":row.get("title"),
          "specialist_role":role,"specialist":specialists.get(role,f"{role}_agent"),
          "attention_units":row.get("attention_units",0),
          "status":"planned_internal_assignment",
          "instruction":f"Analyze and advance the internal planning work for '{row.get('title')}' within current safety and execution eligibility limits."
        })
    out={"generated_at":now(),"assignment_count":len(assignments),"assignments":assignments}
    save(OUT,out)
    report={"generated_at":now(),"assignment_count":len(assignments),"assignments":assignments,
      "automatic_external_write":False,"automatic_customer_contact":False,"automatic_publication":False,
      "automatic_spending":False,"automatic_fund_transfer":False,"automatic_code_changes":False,
      "automatic_merge":False,"automatic_deploy":False,"automatic_destructive_actions":False}
    save(REPORT,report);save(STATE,{"last_planned_at":now(),"assignment_count":len(assignments)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"assignment_count":len(assignments)})
    return {"success":True,"status":"specialist_delegation_plan_complete","report":report}

def status():
    return {"success":True,"status":"specialist_delegation_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(REPORT,{}),"plan":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=delegate() if a=="plan" else status() if a=="status" else {"success":False,"allowed":["plan","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/specialist_delegation_planner.py"

cat > "$CTL/specialistdelegatectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"specialist_delegation_planner.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/specialistdelegatectl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/specialist_delegation_planner.py" "$CTL/specialistdelegatectl"
echo "[2/6] Building specialist delegation plan..."
python "$CTL/specialistdelegatectl" plan
echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"specialist-delegation-planner","enabled":True,"interval_seconds":21600,
"command":["python","companyos/specialistdelegatectl","plan"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2),encoding="utf-8")
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
echo "[4/6] Restarting scheduler..."
python "$CTL/operationsctl" restart
echo "[5/6] Checking status..."
python "$CTL/specialistdelegatectl" status
echo "[6/6] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[r/"agents"/"specialist_delegation_planner.py",r/"companyos"/"specialistdelegatectl",
r/"ceo_memory"/"specialist_delegation_config.json",r/"ceo_memory"/"specialist_delegation_state.json",
r/"ceo_memory"/"specialist_delegation_report.json",r/"ceo_memory"/"specialist_delegation_health.json",
r/"ceo_memory"/"specialist_assignment_plan.json",r/"ceo_memory"/"autonomous_operations_config.json"]
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
if not any(x.get("id")=="specialist-delegation-planner" and x.get("enabled") for x in sched.get("jobs",[])):
    errors.append("Scheduler job missing/disabled")
print("--------------------------------------------");print("Phase 21 Step 17 verification")
print(f"Errors: {len(errors)}");print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 21 STEP 17 INSTALLED"
echo " SPECIALIST DELEGATION PLANNER ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/specialistdelegatectl plan"
echo "  python companyos/specialistdelegatectl status"
