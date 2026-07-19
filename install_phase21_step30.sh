#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"; MEM="$ROOT/ceo_memory"; CTL="$ROOT/companyos"; AGENTS="$ROOT/agents"
cd "$ROOT"; mkdir -p "$MEM" "$CTL" "$AGENTS"

echo "============================================================"
echo " Phase 21 Step 30 - Automatic Validated Insight Refresh"
echo "============================================================"

cat > "$MEM/validated_insight_refresh_config.json" <<'JSON'
{
  "enabled": true,
  "minimum_confidence": 0.5,
  "maximum_results_per_cycle": 50,
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

cat > "$AGENTS/validated_insight_refresh.py" <<'PY'
#!/usr/bin/env python3
import json,sys,hashlib
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"validated_insight_refresh_config.json"
SOURCE=MEM/"specialist_work_results.json"
TARGET=MEM/"validated_insights.json"
STATE=MEM/"validated_insight_refresh_state.json"
REPORT=MEM/"validated_insight_refresh_report.json"
HEALTH=MEM/"validated_insight_refresh_health.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(d,indent=2),encoding="utf-8"); t.replace(p)
def f(v,d=0):
    try:return float(v)
    except:return float(d)
def ident(row):
    raw="|".join(str(row.get(k,"")) for k in ("result_id","work_id","opportunity_id"))
    return "insight-"+hashlib.sha256(raw.encode()).hexdigest()[:20]

def refresh():
    cfg=load(CFG,{})
    rows=load(SOURCE,{}).get("results",[])
    doc=load(TARGET,{"insights":[]})
    insights=doc.get("insights",[])
    seen={x.get("source_result_id") for x in insights if x.get("source_result_id")}
    minimum=f(cfg.get("minimum_confidence",.5),.5)
    maximum=int(cfg.get("maximum_results_per_cycle",50))
    added=[];rejected=[]
    for row in rows:
        if len(added)>=maximum: break
        if row.get("status")!="completed": continue
        rid=row.get("result_id") or row.get("work_id")
        if not rid or rid in seen: continue
        actual=row.get("actual_result")
        if not isinstance(actual,dict):
            rejected.append({"source_result_id":rid,"reason":"missing_structured_result"}); continue
        confidence=f(actual.get("confidence",0),0)
        if confidence<minimum:
            rejected.append({"source_result_id":rid,"reason":"confidence_below_threshold","confidence":confidence}); continue
        insight={
          "insight_id":ident(row),
          "source_result_id":rid,
          "work_id":row.get("work_id"),
          "plan_id":row.get("plan_id"),
          "decision_id":row.get("decision_id"),
          "opportunity_id":row.get("opportunity_id"),
          "summary":actual.get("summary"),
          "findings":actual.get("findings",[]),
          "recommendations":actual.get("recommendations",[]),
          "risks":actual.get("risks",[]),
          "next_internal_actions":actual.get("next_internal_actions",[]),
          "confidence":confidence,
          "validation_status":"validated_for_internal_reasoning",
          "execution_boundary":"internal_non_destructive_only",
          "validated_at":now()
        }
        insights.append(insight);added.append(insight);seen.add(rid)
    save(TARGET,{"generated_at":now(),"insight_count":len(insights),"insights":insights})
    report={"generated_at":now(),"added_count":len(added),"rejected_count":len(rejected),
      "total_insight_count":len(insights),"added":added,"rejected":rejected,
      "automatic_external_write":False,"automatic_customer_contact":False,"automatic_publication":False,
      "automatic_spending":False,"automatic_fund_transfer":False,"automatic_code_changes":False,
      "automatic_merge":False,"automatic_deploy":False,"automatic_destructive_actions":False}
    save(REPORT,report)
    save(STATE,{"last_refresh_at":now(),"added_count":len(added),"total_insight_count":len(insights)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"total_insight_count":len(insights)})
    return {"success":True,"status":"validated_insight_refresh_complete","report":report}

def status():
    return {"success":True,"status":"validated_insight_refresh_status",
      "state":load(STATE,{}),"health":load(HEALTH,{}),"report":load(REPORT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=refresh() if a=="refresh" else status() if a=="status" else {"success":False,"allowed":["refresh","status"]}
print(json.dumps(r,indent=2)); raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/validated_insight_refresh.py"

cat > "$CTL/insightrefreshctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"validated_insight_refresh.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/insightrefreshctl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/validated_insight_refresh.py" "$CTL/insightrefreshctl"
echo "[2/6] Refreshing validated insights..."
python "$CTL/insightrefreshctl" refresh
echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text()); jobs=d.setdefault("jobs",[])
job={"id":"validated-insight-refresh","enabled":True,"interval_seconds":1800,
"command":["python","companyos/insightrefreshctl","refresh"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2),encoding="utf-8")
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
echo "[4/6] Restarting operations scheduler..."
python "$CTL/operationsctl" restart
echo "[5/6] Checking status..."
python "$CTL/insightrefreshctl" status
echo "[6/6] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos"; errors=[]
req=[r/"agents"/"validated_insight_refresh.py",r/"companyos"/"insightrefreshctl",
r/"ceo_memory"/"validated_insight_refresh_config.json",r/"ceo_memory"/"validated_insight_refresh_state.json",
r/"ceo_memory"/"validated_insight_refresh_report.json",r/"ceo_memory"/"validated_insight_refresh_health.json",
r/"ceo_memory"/"validated_insights.json",r/"ceo_memory"/"autonomous_operations_config.json"]
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
if not any(x.get("id")=="validated-insight-refresh" and x.get("enabled") for x in sched.get("jobs",[])):
    errors.append("Scheduler job missing/disabled")
print("--------------------------------------------")
print("Phase 21 Step 30 verification")
print(f"Errors: {len(errors)}"); print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY
echo
echo "============================================================"
echo " PHASE 21 STEP 30 INSTALLED"
echo " AUTOMATIC VALIDATED INSIGHT REFRESH ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/insightrefreshctl refresh"
echo "  python companyos/insightrefreshctl status"
