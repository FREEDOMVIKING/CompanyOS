#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"; AGENTS="$ROOT/agents"; CTL="$ROOT/companyos"; MEM="$ROOT/ceo_memory"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 21 Step 21 - CEO Insight Decision Synthesizer"
echo "============================================================"

cat > "$MEM/ceo_insight_decision_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_internal_synthesis": true,
  "maximum_decisions_per_cycle": 10,
  "minimum_confidence": 0.5,
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

cat > "$AGENTS/ceo_insight_decision_synthesizer.py" <<'PY'
#!/usr/bin/env python3
import json,sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"ceo_insight_decision_config.json"
INSIGHTS=MEM/"ceo_specialist_insights.json"
STATE=MEM/"ceo_insight_decision_state.json"
REPORT=MEM/"ceo_insight_decision_report.json"
HEALTH=MEM/"ceo_insight_decision_health.json"
OUT=MEM/"ceo_decision_candidates.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def num(v,d=0):
    try:return float(v)
    except:return float(d)

def synthesize():
    cfg=load(CFG,{})
    rows=load(INSIGHTS,{}).get("insights",[])
    maximum=int(cfg.get("maximum_decisions_per_cycle",10))
    minimum=num(cfg.get("minimum_confidence",.5))
    decisions=[];rejected=[]

    for row in rows:
        confidence=num(row.get("confidence",0))
        if confidence<minimum:
            rejected.append({"insight_id":row.get("insight_id"),"reason":"confidence_below_threshold"})
            continue
        recs=row.get("recommendations",[]) or []
        actions=row.get("next_internal_actions",[]) or []
        risks=row.get("risks",[]) or []
        decisions.append({
          "decision_id":f"{row.get('insight_id')}-decision",
          "opportunity_id":row.get("opportunity_id"),"title":row.get("title"),
          "source_insight_id":row.get("insight_id"),"confidence":confidence,
          "recommended_direction":recs[0] if recs else "continue_internal_analysis",
          "supporting_recommendations":recs,
          "known_risks":risks,
          "proposed_internal_actions":actions,
          "decision_class":"internal_candidate",
          "status":"ready_for_ceo_internal_review",
          "created_at":now()
        })
        if len(decisions)>=maximum:break

    payload={"generated_at":now(),"decision_count":len(decisions),"decisions":decisions,
      "note":"Decision candidates are internal recommendations only and grant no new execution authority."}
    save(OUT,payload)
    report={"generated_at":now(),"decision_count":len(decisions),"rejected_count":len(rejected),
      "decisions":decisions,"rejected":rejected,
      "automatic_external_write":False,"automatic_customer_contact":False,"automatic_publication":False,
      "automatic_spending":False,"automatic_fund_transfer":False,"automatic_code_changes":False,
      "automatic_merge":False,"automatic_deploy":False,"automatic_destructive_actions":False}
    save(REPORT,report)
    save(STATE,{"last_synthesized_at":now(),"decision_count":len(decisions),"rejected_count":len(rejected)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"decision_count":len(decisions)})
    return {"success":True,"status":"ceo_insight_decision_synthesis_complete","report":report}

def status():
    return {"success":True,"status":"ceo_insight_decision_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(REPORT,{}),"decisions":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=synthesize() if a=="synthesize" else status() if a=="status" else {"success":False,"allowed":["synthesize","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/ceo_insight_decision_synthesizer.py"

cat > "$CTL/ceoinsightdecisionctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"ceo_insight_decision_synthesizer.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/ceoinsightdecisionctl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/ceo_insight_decision_synthesizer.py" "$CTL/ceoinsightdecisionctl"
echo "[2/6] Synthesizing CEO decision candidates..."
python "$CTL/ceoinsightdecisionctl" synthesize
echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"ceo-insight-decision-synthesis","enabled":True,"interval_seconds":21600,
"command":["python","companyos/ceoinsightdecisionctl","synthesize"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2),encoding="utf-8")
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
echo "[4/6] Restarting scheduler..."
python "$CTL/operationsctl" restart
echo "[5/6] Checking status..."
python "$CTL/ceoinsightdecisionctl" status
echo "[6/6] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[r/"agents"/"ceo_insight_decision_synthesizer.py",r/"companyos"/"ceoinsightdecisionctl",
r/"ceo_memory"/"ceo_insight_decision_config.json",r/"ceo_memory"/"ceo_insight_decision_state.json",
r/"ceo_memory"/"ceo_insight_decision_report.json",r/"ceo_memory"/"ceo_insight_decision_health.json",
r/"ceo_memory"/"ceo_decision_candidates.json",r/"ceo_memory"/"autonomous_operations_config.json"]
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
if not any(x.get("id")=="ceo-insight-decision-synthesis" and x.get("enabled") for x in sched.get("jobs",[])):
    errors.append("Scheduler job missing/disabled")
print("--------------------------------------------");print("Phase 21 Step 21 verification")
print(f"Errors: {len(errors)}");print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 21 STEP 21 INSTALLED"
echo " CEO INSIGHT DECISION SYNTHESIZER ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/ceoinsightdecisionctl synthesize"
echo "  python companyos/ceoinsightdecisionctl status"
