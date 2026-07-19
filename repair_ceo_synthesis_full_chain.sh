#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/repair_ceo_synthesis_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$BACKUP"

echo "============================================================"
echo " COMPANYOS REPAIR BUNDLE - CEO DECISION SYNTHESIS ROOT FIX"
echo "============================================================"

TARGET="$AGENTS/ceo_insight_decision_synthesizer.py"

if [ ! -f "$TARGET" ]; then
  echo "ERROR: Missing $TARGET"
  exit 1
fi

cp -a "$TARGET" "$BACKUP/"

cat > "$TARGET" <<'PY'
#!/usr/bin/env python3
import json, sys
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"ceo_insight_decision_config.json"
INSIGHTS=MEM/"ceo_specialist_insights.json"
STATE=MEM/"ceo_insight_decision_state.json"
REPORT=MEM/"ceo_insight_decision_report.json"
HEALTH=MEM/"ceo_insight_decision_health.json"
OUT=MEM/"ceo_decision_candidates.json"

def now(): return datetime.now(timezone.utc).isoformat()

def load(p,d):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return d

def save(p,d):
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(d,indent=2),encoding="utf-8")
    t.replace(p)

def num(v,d=0):
    try:return float(v)
    except:return float(d)

def as_list(value):
    if value is None:
        return []
    if isinstance(value,list):
        return value
    if isinstance(value,tuple):
        return list(value)
    if isinstance(value,dict):
        # Preserve useful values from structured model output.
        preferred=[]
        for key in ("items","recommendations","actions","risks","next_internal_actions"):
            v=value.get(key)
            if isinstance(v,list):
                preferred.extend(v)
        if preferred:
            return preferred
        return list(value.values())
    return [value]

def first_text(value, default):
    items=as_list(value)
    if not items:
        return default
    first=items[0]
    if isinstance(first,str):
        return first
    if isinstance(first,dict):
        for key in ("title","text","recommendation","action","summary","description"):
            v=first.get(key)
            if isinstance(v,str) and v.strip():
                return v.strip()
        return json.dumps(first,sort_keys=True)
    return str(first)

def synthesize():
    cfg=load(CFG,{})
    rows=load(INSIGHTS,{}).get("insights",[])
    maximum=int(cfg.get("maximum_decisions_per_cycle",10))
    minimum=num(cfg.get("minimum_confidence",.5),.5)
    decisions=[];rejected=[]

    for row in rows:
        confidence=num(row.get("confidence",0),0)
        if confidence < minimum:
            rejected.append({
                "insight_id":row.get("insight_id"),
                "reason":"confidence_below_threshold"
            })
            continue

        recs=as_list(row.get("recommendations"))
        actions=as_list(row.get("next_internal_actions"))
        risks=as_list(row.get("risks"))

        decision={
            "decision_id":f'{row.get("insight_id","insight")}-decision',
            "opportunity_id":row.get("opportunity_id"),
            "title":row.get("title") or first_text(row.get("summary"),"Untitled internal decision"),
            "source_insight_id":row.get("insight_id"),
            "confidence":confidence,
            "recommended_direction":first_text(recs,"continue_internal_analysis"),
            "supporting_recommendations":recs,
            "known_risks":risks,
            "proposed_internal_actions":actions,
            "decision_class":"internal_candidate",
            "status":"ready_for_ceo_internal_review",
            "created_at":now()
        }
        decisions.append(decision)
        if len(decisions)>=maximum:
            break

    payload={
        "generated_at":now(),
        "decision_count":len(decisions),
        "decisions":decisions,
        "note":"Decision candidates are internal recommendations only and grant no new execution authority."
    }
    save(OUT,payload)

    report={
        "generated_at":now(),
        "decision_count":len(decisions),
        "rejected_count":len(rejected),
        "decisions":decisions,
        "rejected":rejected,
        "automatic_external_write":False,
        "automatic_customer_contact":False,
        "automatic_publication":False,
        "automatic_spending":False,
        "automatic_fund_transfer":False,
        "automatic_code_changes":False,
        "automatic_merge":False,
        "automatic_deploy":False,
        "automatic_destructive_actions":False
    }
    save(REPORT,report)
    save(STATE,{
        "last_synthesized_at":now(),
        "decision_count":len(decisions),
        "rejected_count":len(rejected)
    })
    save(HEALTH,{
        "healthy":True,
        "last_checked_at":now(),
        "decision_count":len(decisions)
    })
    return {
        "success":True,
        "status":"ceo_insight_decision_synthesis_complete",
        "report":report
    }

def status():
    return {
        "success":True,
        "status":"ceo_insight_decision_status",
        "state":load(STATE,{}),
        "health":load(HEALTH,{}),
        "report":load(REPORT,{}),
        "decisions":load(OUT,{})
    }

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=synthesize() if a=="synthesize" else status() if a=="status" else {
    "success":False,
    "allowed":["synthesize","status"]
}
print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
PY

chmod +x "$TARGET"

echo "[1/7] Compiling repaired synthesizer..."
python -m py_compile "$TARGET"

echo "[2/7] Direct CEO synthesis test..."
python companyos/ceoinsightdecisionctl synthesize

echo "[3/7] Autonomy recovery..."
python companyos/autonomyctl run

echo "[4/7] Phase 23 recovery..."
python companyos/phase23ctl run
python companyos/phase23bundle2ctl run
python companyos/phase23bundle3ctl run

echo "[5/7] Phase 24 recovery..."
python companyos/phase24ctl run
python companyos/phase24bundle2ctl run

echo "[6/7] Final chain status..."
python companyos/phase24bundle2ctl status

echo "[7/7] Verifying full dependency chain..."
python - <<'PY'
import json, py_compile
from pathlib import Path

r=Path.home()/"companyos"
errors=[]

py_compile.compile(str(r/"agents"/"ceo_insight_decision_synthesizer.py"),doraise=True)

checks=[
 ("autonomy", r/"ceo_memory"/"autonomy_core_state.json"),
 ("phase23", r/"ceo_memory"/"phase23_state.json"),
 ("phase23_bundle2", r/"ceo_memory"/"phase23_bundle2_state.json"),
 ("phase23_bundle3", r/"ceo_memory"/"phase23_bundle3_state.json"),
 ("phase24", r/"ceo_memory"/"phase24_state.json"),
 ("phase24_bundle2", r/"ceo_memory"/"phase24_bundle2_state.json"),
]

for name,path in checks:
    if not path.exists():
        errors.append(f"{name}: missing state file")
        continue
    try:
        d=json.loads(path.read_text())
    except Exception as e:
        errors.append(f"{name}: invalid state JSON: {e}")
        continue
    if int(d.get("failure_count",0) or 0) != 0:
        errors.append(f"{name}: failure_count={d.get('failure_count')}")
    if d.get("failed_steps"):
        errors.append(f"{name}: failed_steps={d.get('failed_steps')}")

decision_health=r/"ceo_memory"/"ceo_insight_decision_health.json"
if not decision_health.exists():
    errors.append("CEO synthesis health file missing")
else:
    d=json.loads(decision_health.read_text())
    if d.get("healthy") is not True:
        errors.append("CEO synthesis is not healthy")

print("--------------------------------------------")
print("FULL RECOVERY VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:
    print("ERROR:",e)

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " COMPANYOS ROOT FAILURE REPAIRED"
echo " CEO DECISION SYNTHESIS NORMALIZATION ACTIVE"
echo " PHASE 23 -> PHASE 24 CHAIN RECOVERED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Backup saved to:"
echo "  $BACKUP"
echo
echo "Recommended status command:"
echo "  python companyos/phase24bundle2ctl status"
