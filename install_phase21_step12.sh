#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"; AGENTS="$ROOT/agents"; CTL="$ROOT/companyos"; MEM="$ROOT/ceo_memory"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 21 Step 12 - Portfolio Capacity & Concentration Guard"
echo "============================================================"

cat > "$MEM/portfolio_capacity_config.json" <<'JSON'
{
  "enabled": true,
  "maximum_active_opportunities": 5,
  "maximum_per_category": 2,
  "minimum_final_score": 50,
  "automatic_rebalancing": true,
  "automatic_external_write": false,
  "automatic_customer_contact": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_code_changes": false,
  "automatic_merge": false,
  "automatic_deploy": false,
  "automatic_destructive_actions": false
}
JSON

cat > "$AGENTS/portfolio_capacity_guard.py" <<'PY'
#!/usr/bin/env python3
import json,sys
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"portfolio_capacity_config.json"
PORT=MEM/"active_opportunity_portfolio.json"
STATE=MEM/"portfolio_capacity_state.json"
REPORT=MEM/"portfolio_capacity_report.json"
HEALTH=MEM/"portfolio_capacity_health.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def evaluate():
    cfg=load(CFG,{})
    portfolio=load(PORT,{"opportunities":[]})
    rows=portfolio.get("opportunities",[])
    max_active=int(cfg.get("maximum_active_opportunities",5))
    max_cat=int(cfg.get("maximum_per_category",2))
    min_score=float(cfg.get("minimum_final_score",50))
    accepted=[]; rejected=[]; counts=Counter()

    ordered=sorted(rows,key=lambda x:float(x.get("final_opportunity_score",0) or 0),reverse=True)
    for row in ordered:
        category=row.get("category") or "uncategorized"
        score=float(row.get("final_opportunity_score",0) or 0)
        reason=None
        if score < min_score: reason="below_minimum_score"
        elif len(accepted)>=max_active: reason="portfolio_capacity_reached"
        elif counts[category]>=max_cat: reason="category_concentration_limit"
        if reason:
            rejected.append({"id":row.get("id"),"title":row.get("title"),"reason":reason})
        else:
            accepted.append(row);counts[category]+=1

    report={
      "generated_at":now(),"input_count":len(rows),"accepted_count":len(accepted),
      "rejected_count":len(rejected),"category_counts":dict(counts),
      "accepted":accepted,"rejected":rejected,
      "automatic_external_write":False,"automatic_customer_contact":False,
      "automatic_publication":False,"automatic_spending":False,"automatic_code_changes":False,
      "automatic_merge":False,"automatic_deploy":False,"automatic_destructive_actions":False
    }
    save(REPORT,report)
    save(STATE,{"last_evaluated_at":now(),"accepted_count":len(accepted),
                "rejected_count":len(rejected),"category_counts":dict(counts)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"violations_prevented":len(rejected)})
    return {"success":True,"status":"portfolio_capacity_evaluation_complete","report":report}

def status():
    return {"success":True,"status":"portfolio_capacity_status","state":load(STATE,{}),
            "health":load(HEALTH,{}),"report":load(REPORT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=evaluate() if a in ("evaluate","rebalance") else status() if a=="status" else {"success":False,"allowed":["evaluate","rebalance","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/portfolio_capacity_guard.py"

cat > "$CTL/portfoliocapacityctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"portfolio_capacity_guard.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/portfoliocapacityctl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/portfolio_capacity_guard.py" "$CTL/portfoliocapacityctl"
echo "[2/6] Evaluating portfolio capacity..."
python "$CTL/portfoliocapacityctl" evaluate
echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"portfolio-capacity-guard","enabled":True,"interval_seconds":21600,
"command":["python","companyos/portfoliocapacityctl","evaluate"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2),encoding="utf-8")
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
echo "[4/6] Restarting scheduler..."
python "$CTL/operationsctl" restart
echo "[5/6] Checking status..."
python "$CTL/portfoliocapacityctl" status
echo "[6/6] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[r/"agents"/"portfolio_capacity_guard.py",r/"companyos"/"portfoliocapacityctl",
r/"ceo_memory"/"portfolio_capacity_config.json",r/"ceo_memory"/"portfolio_capacity_state.json",
r/"ceo_memory"/"portfolio_capacity_report.json",r/"ceo_memory"/"portfolio_capacity_health.json",
r/"ceo_memory"/"autonomous_operations_config.json"]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:2]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
cfg=json.loads(req[2].read_text())
for k in ["automatic_external_write","automatic_customer_contact","automatic_publication","automatic_spending",
"automatic_code_changes","automatic_merge","automatic_deploy","automatic_destructive_actions"]:
    if cfg.get(k) is not False:errors.append(f"{k} must remain disabled")
sched=json.loads(req[6].read_text())
if not any(x.get("id")=="portfolio-capacity-guard" and x.get("enabled") for x in sched.get("jobs",[])):
    errors.append("Scheduler job missing/disabled")
print("--------------------------------------------");print("Phase 21 Step 12 verification")
print(f"Errors: {len(errors)}");print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 21 STEP 12 INSTALLED"
echo " PORTFOLIO CAPACITY & CONCENTRATION GUARD ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/portfoliocapacityctl evaluate"
echo "  python companyos/portfoliocapacityctl status"
