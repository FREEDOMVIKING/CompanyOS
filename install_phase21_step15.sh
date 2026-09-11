#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"; AGENTS="$ROOT/agents"; CTL="$ROOT/companyos"; MEM="$ROOT/ceo_memory"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 21 Step 15 - Portfolio Performance & Capital Readiness"
echo "============================================================"

cat > "$MEM/portfolio_performance_config.json" <<'JSON'
{
  "enabled": true,
  "minimum_score_for_resource_priority": 60,
  "minimum_learning_samples": 2,
  "maximum_priority_candidates": 5,
  "automatic_internal_resource_prioritization": true,
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

cat > "$AGENTS/portfolio_performance_manager.py" <<'PY'
#!/usr/bin/env python3
import json,sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"portfolio_performance_config.json"
PORT=MEM/"rebalanced_opportunity_portfolio.json"
OUTCOMES=MEM/"opportunity_action_scores.json"
STATE=MEM/"portfolio_performance_state.json"
REPORT=MEM/"portfolio_performance_report.json"
HEALTH=MEM/"portfolio_performance_health.json"
PRIORITIES=MEM/"portfolio_resource_priorities.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def num(v,d=0):
    try:return float(v)
    except:return float(d)

def evaluate():
    cfg=load(CFG,{})
    rows=load(PORT,{}).get("opportunities",[])
    action_scores=load(OUTCOMES,{}).get("actions",{})
    minimum=num(cfg.get("minimum_score_for_resource_priority",60))
    min_samples=int(cfg.get("minimum_learning_samples",2))
    maximum=int(cfg.get("maximum_priority_candidates",5))
    ranked=[]

    for row in rows:
        oid=str(row.get("id") or "")
        related=[v for k,v in action_scores.items() if oid and k.startswith(oid+"-")]
        samples=sum(int(x.get("samples",0) or 0) for x in related)
        learned=(sum(num(x.get("score",50),50) for x in related)/len(related)) if related else 50.0
        strategic=num(row.get("final_opportunity_score",0))
        readiness=round((strategic*.7)+(learned*.3),2) if samples>=min_samples else round(strategic,2)
        ranked.append({
          "id":row.get("id"),"title":row.get("title"),"category":row.get("category"),
          "strategic_score":round(strategic,2),"learned_score":round(learned,2),
          "learning_samples":samples,"resource_readiness_score":readiness,
          "priority_eligible":readiness>=minimum,
          "recommendation":"prioritize_internal_resources" if readiness>=minimum else "observe"
        })

    ranked.sort(key=lambda x:(x["resource_readiness_score"],x["learning_samples"]),reverse=True)
    priority=[x for x in ranked if x["priority_eligible"]][:maximum]
    save(PRIORITIES,{"generated_at":now(),"candidates":priority,
      "note":"Internal prioritization only; no spending or fund movement is authorized."})

    report={"generated_at":now(),"evaluated_count":len(ranked),"priority_count":len(priority),
      "ranked":ranked,"priority_candidates":priority,
      "automatic_external_write":False,"automatic_customer_contact":False,
      "automatic_publication":False,"automatic_spending":False,"automatic_fund_transfer":False,
      "automatic_code_changes":False,"automatic_merge":False,"automatic_deploy":False,
      "automatic_destructive_actions":False}
    save(REPORT,report)
    save(STATE,{"last_evaluated_at":now(),"evaluated_count":len(ranked),"priority_count":len(priority),
      "top_candidate":priority[0]["title"] if priority else None})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"evaluated_count":len(ranked)})
    return {"success":True,"status":"portfolio_performance_evaluation_complete","report":report}

def status():
    return {"success":True,"status":"portfolio_performance_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(REPORT,{}),"priorities":load(PRIORITIES,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=evaluate() if a=="evaluate" else status() if a=="status" else {"success":False,"allowed":["evaluate","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/portfolio_performance_manager.py"

cat > "$CTL/portfolioperformancectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"portfolio_performance_manager.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/portfolioperformancectl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/portfolio_performance_manager.py" "$CTL/portfolioperformancectl"
echo "[2/6] Evaluating portfolio performance..."
python "$CTL/portfolioperformancectl" evaluate
echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"portfolio-performance-readiness","enabled":True,"interval_seconds":21600,
"command":["python","companyos/portfolioperformancectl","evaluate"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2),encoding="utf-8")
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
echo "[4/6] Restarting scheduler..."
python "$CTL/operationsctl" restart
echo "[5/6] Checking status..."
python "$CTL/portfolioperformancectl" status
echo "[6/6] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[r/"agents"/"portfolio_performance_manager.py",r/"companyos"/"portfolioperformancectl",
r/"ceo_memory"/"portfolio_performance_config.json",r/"ceo_memory"/"portfolio_performance_state.json",
r/"ceo_memory"/"portfolio_performance_report.json",r/"ceo_memory"/"portfolio_performance_health.json",
r/"ceo_memory"/"portfolio_resource_priorities.json",r/"ceo_memory"/"autonomous_operations_config.json"]
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
if not any(x.get("id")=="portfolio-performance-readiness" and x.get("enabled") for x in sched.get("jobs",[])):
    errors.append("Scheduler job missing/disabled")
print("--------------------------------------------");print("Phase 21 Step 15 verification")
print(f"Errors: {len(errors)}");print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 21 STEP 15 INSTALLED"
echo " PORTFOLIO PERFORMANCE & CAPITAL READINESS ENGINE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/portfolioperformancectl evaluate"
echo "  python companyos/portfolioperformancectl status"
