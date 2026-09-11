#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 21 Step 4 - Opportunity-to-Action Translation Engine"
echo "============================================================"

cat > "$MEM/opportunity_translation_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_translation": true,
  "maximum_actions": 10,
  "default_category": "internal_read_only",
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

cat > "$AGENTS/opportunity_action_translator.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"opportunity_translation_config.json"
QUEUE=MEM/"opportunity_activation_queue.json"
ELIGIBILITY=MEM/"execution_eligibility_report.json"
STATE=MEM/"opportunity_translation_state.json"
REPORT=MEM/"opportunity_translation_report.json"
HEALTH=MEM/"opportunity_translation_health.json"
ACTION_QUEUE=MEM/"opportunity_action_queue.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(d,indent=2),encoding="utf-8"); t.replace(p)

def translate_text(item:dict[str,Any]):
    title=item.get("title") or "Untitled opportunity"
    recommendation=item.get("recommendation") or ""
    category=item.get("category") or "internal_read_only"
    out=[{
        "action_id":f"{item.get('id') or 'opp'}-analyze",
        "title":f"Analyze opportunity: {title}",
        "category":"internal_read_only",
        "priority":item.get("alignment_score",50),
        "instruction":recommendation or f"Analyze the opportunity '{title}' and produce the next best internal step."
    }]
    if category in {"internal_reversible","internal_read_only","external_read_only"}:
        out.append({
            "action_id":f"{item.get('id') or 'opp'}-prepare",
            "title":f"Prepare next action for: {title}",
            "category":"internal_reversible",
            "priority":max(1,float(item.get("alignment_score",50))-5),
            "instruction":f"Prepare a reversible internal action plan for '{title}' without contacting customers, publishing, spending, deploying, or changing external systems."
        })
    return out

def translate():
    cfg=load(CFG,{})
    queue=load(QUEUE,{})
    eligibility=load(ELIGIBILITY,{})
    matrix=eligibility.get("eligibility",{})
    maximum=int(cfg.get("maximum_actions",10))
    translated=[]; blocked=[]
    for candidate in queue.get("candidates",[]):
        for action in translate_text(candidate):
            category=action.get("category",cfg.get("default_category","internal_read_only"))
            if not bool(matrix.get(category,False)):
                blocked.append({**action,"reason":"category_not_eligible"})
                continue
            translated.append(action)
            if len(translated)>=maximum: break
        if len(translated)>=maximum: break
    save(ACTION_QUEUE,{"generated_at":now(),"actions":translated})
    report={"generated_at":now(),"translated_count":len(translated),"blocked_count":len(blocked),
            "actions":translated,"blocked":blocked,
            "automatic_external_write":False,"automatic_customer_contact":False,
            "automatic_publication":False,"automatic_spending":False,
            "automatic_code_changes":False,"automatic_merge":False,
            "automatic_deploy":False,"automatic_destructive_actions":False}
    save(REPORT,report)
    save(STATE,{"last_translated_at":now(),"translated_count":len(translated),"blocked_count":len(blocked)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"translated_count":len(translated)})
    return {"success":True,"status":"opportunity_translation_complete","report":report}

def status():
    return {"success":True,"status":"opportunity_translation_status","state":load(STATE,{}),
            "health":load(HEALTH,{}),"report":load(REPORT,{}),"queue":load(ACTION_QUEUE,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=translate() if a=="translate" else status() if a=="status" else {"success":False,"allowed":["translate","status"]}
print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
PY

chmod +x "$AGENTS/opportunity_action_translator.py"

cat > "$CTL/opportunitytranslatectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"opportunity_action_translator.py"),*sys.argv[1:]],cwd=r))
PY

chmod +x "$CTL/opportunitytranslatectl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/opportunity_action_translator.py" "$CTL/opportunitytranslatectl"

echo "[2/6] Translating activated opportunities..."
python "$CTL/opportunitytranslatectl" translate

echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text())
jobs=d.setdefault("jobs",[])
job={"id":"opportunity-action-translation","enabled":True,"interval_seconds":21600,
     "command":["python","companyos/opportunitytranslatectl","translate"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2),encoding="utf-8")
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY

echo "[4/6] Restarting scheduler..."
python "$CTL/operationsctl" restart

echo "[5/6] Checking translation status..."
python "$CTL/opportunitytranslatectl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
root=Path.home()/"companyos"; errors=[]
required=[
 root/"agents"/"opportunity_action_translator.py",
 root/"companyos"/"opportunitytranslatectl",
 root/"ceo_memory"/"opportunity_translation_config.json",
 root/"ceo_memory"/"opportunity_translation_state.json",
 root/"ceo_memory"/"opportunity_translation_report.json",
 root/"ceo_memory"/"opportunity_translation_health.json",
 root/"ceo_memory"/"opportunity_action_queue.json",
 root/"ceo_memory"/"autonomous_operations_config.json"]
for p in required:
    if not p.exists() or p.stat().st_size<=0: errors.append(f"Missing/empty: {p}")
for p in required[:2]:
    try: py_compile.compile(str(p),doraise=True)
    except Exception as e: errors.append(str(e))
cfg=json.loads(required[2].read_text())
for k in ["automatic_external_write","automatic_customer_contact","automatic_publication","automatic_spending",
          "automatic_code_changes","automatic_merge","automatic_deploy","automatic_destructive_actions"]:
    if cfg.get(k) is not False: errors.append(f"{k} must remain disabled")
sched=json.loads(required[7].read_text())
job=next((x for x in sched.get("jobs",[]) if x.get("id")=="opportunity-action-translation"),None)
if not job or job.get("enabled") is not True: errors.append("Opportunity translation scheduler job missing/disabled")
print("--------------------------------------------")
print("Phase 21 Step 4 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors: print("ERROR:",e)
if errors: raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 21 STEP 4 INSTALLED"
echo " OPPORTUNITY-TO-ACTION TRANSLATION ENGINE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/opportunitytranslatectl translate"
echo "  python companyos/opportunitytranslatectl status"
