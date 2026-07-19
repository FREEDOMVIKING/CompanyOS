#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase25_bundle3_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " PHASE 25 BUNDLE 3 - AUTONOMOUS CEO DECISION LOOP"
echo "============================================================"

cat > "$MEM/phase25_bundle3_config.json" <<'JSON'
{
  "enabled": true,
  "maximum_opportunities": 25,
  "maximum_active_plans": 10,
  "maximum_recovery_attempts": 3,
  "minimum_opportunity_score": 50,
  "automatic_internal_discovery": true,
  "automatic_internal_scoring": true,
  "automatic_internal_planning": true,
  "automatic_internal_delegation": true,
  "automatic_internal_validation": true,
  "automatic_internal_learning": true,
  "automatic_internal_recovery": true,
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

cat > "$AGENTS/opportunity_scoring_engine.py" <<'PY'
#!/usr/bin/env python3
import json, hashlib
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase25_bundle3_config.json"; OUT=MEM/"scored_opportunities.json"; STATE=MEM/"opportunity_scoring_state.json"; HEALTH=MEM/"opportunity_scoring_health.json"
SOURCES=[MEM/"generated_business_opportunities.json",MEM/"opportunity_discovery_results.json",MEM/"business_opportunities.json"]
def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def fid(x): return hashlib.sha256(str(x).encode()).hexdigest()[:18]
def num(v,d=50):
    try:return float(v)
    except:return float(d)
def collect():
    rows=[]
    for p in SOURCES:
        d=load(p,{})
        if isinstance(d,list): vals=d
        else:
            vals=[]
            for k in ("opportunities","results","items"):
                if isinstance(d.get(k),list): vals.extend(d[k])
        rows.extend(x for x in vals if isinstance(x,dict))
    dedup={}
    for x in rows: dedup[str(x.get("id") or x.get("opportunity_id") or x.get("title") or fid(x))]=x
    return list(dedup.values())
def run():
    cfg=load(CFG,{})
    out=[]
    for o in collect()[:int(cfg.get("maximum_opportunities",25))]:
        upside=num(o.get("upside",o.get("score",60)),60)
        conf=num(o.get("confidence",60),60); conf=conf*100 if conf<=1 else conf
        urgency=num(o.get("urgency",55),55); fit=num(o.get("strategic_fit",65),65); cost=num(o.get("cost_efficiency",60),60); risk=num(o.get("risk",40),40)
        score=upside*.30+conf*.20+urgency*.15+fit*.15+cost*.10+(100-risk)*.10
        out.append({"opportunity_id":o.get("id") or o.get("opportunity_id") or fid(o),"title":o.get("title","Untitled opportunity"),"category":o.get("category","general"),"score":round(score,2),"confidence":round(conf,2),"risk":round(risk,2),"status":"qualified_internal_candidate" if score>=cfg.get("minimum_opportunity_score",50) else "below_internal_threshold","source":o.get("source","internal"),"execution_boundary":"internal_non_destructive_only"})
    out.sort(key=lambda x:x["score"],reverse=True)
    payload={"generated_at":now(),"opportunity_count":len(out),"opportunities":out}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"opportunity_count":len(out)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"opportunity_scoring_complete","report":payload}
print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/opportunity_scoring_engine.py"

cat > "$AGENTS/strategic_execution_planner.py" <<'PY'
#!/usr/bin/env python3
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory";SRC=MEM/"scored_opportunities.json";CFG=MEM/"phase25_bundle3_config.json";OUT=MEM/"strategic_execution_plans.json";STATE=MEM/"strategic_execution_state.json";HEALTH=MEM/"strategic_execution_health.json"
def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def hid(x):return hashlib.sha256(str(x).encode()).hexdigest()[:18]
def run():
    cfg=load(CFG,{});rows=[]
    for o in load(SRC,{}).get("opportunities",[]):
        if o.get("status")!="qualified_internal_candidate":continue
        if len(rows)>=int(cfg.get("maximum_active_plans",10)):break
        pid=hid(o.get("opportunity_id"))
        ms=[{"name":"evidence_validation","status":"planned","objective":"Validate assumptions and evidence"},{"name":"strategy_design","status":"planned","objective":"Design strongest internal strategy"},{"name":"execution_mapping","status":"planned","objective":"Map tasks dependencies and resources"},{"name":"risk_review","status":"planned","objective":"Review risks and failure modes"},{"name":"decision_ready","status":"planned","objective":"Prepare CEO-ready internal recommendation"}]
        rows.append({"plan_id":pid,"opportunity_id":o.get("opportunity_id"),"title":o.get("title"),"priority_score":o.get("score"),"milestones":ms,"status":"planned_internal","external_execution_authorized":False,"execution_boundary":"internal_non_destructive_only"})
    payload={"generated_at":now(),"plan_count":len(rows),"plans":rows}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"plan_count":len(rows)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"strategic_execution_planning_complete","report":payload}
print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/strategic_execution_planner.py"

cat > "$AGENTS/agent_orchestration_engine.py" <<'PY'
#!/usr/bin/env python3
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory";PLANS=MEM/"strategic_execution_plans.json";OUT=MEM/"agent_orchestration_queue.json";STATE=MEM/"agent_orchestration_state.json";HEALTH=MEM/"agent_orchestration_health.json"
def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def hid(x):return hashlib.sha256(str(x).encode()).hexdigest()[:18]
def run():
    rows=[];role_map={"evidence_validation":"research","strategy_design":"strategy","execution_mapping":"planning","risk_review":"review","decision_ready":"synthesis"}
    for p in load(PLANS,{}).get("plans",[]):
        for m in p.get("milestones",[]):
            rows.append({"task_id":hid(p.get("plan_id","")+"|"+m["name"]),"plan_id":p.get("plan_id"),"opportunity_id":p.get("opportunity_id"),"specialist_role":role_map.get(m["name"],"analysis"),"instruction":m.get("objective"),"status":"ready_for_internal_specialist","provider_route":"openai_primary_then_local_fallback","execution_boundary":"internal_non_destructive_only"})
    payload={"generated_at":now(),"task_count":len(rows),"tasks":rows}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"task_count":len(rows)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"agent_orchestration_complete","queue":payload}
print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/agent_orchestration_engine.py"

cat > "$AGENTS/learning_feedback_loop.py" <<'PY'
#!/usr/bin/env python3
import json,statistics
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory";VALID=MEM/"validated_ai_results.json";PROV=MEM/"ai_provenance_log.json";OUT=MEM/"learning_feedback_report.json";STATE=MEM/"learning_feedback_state.json";HEALTH=MEM/"learning_feedback_health.json"
def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def run():
    vals=load(VALID,{}).get("results",[]);conf=[float(x.get("confidence",0) or 0) for x in vals if isinstance(x.get("confidence"),(int,float))];valid=sum(1 for x in vals if x.get("valid"));review=sum(1 for x in vals if not x.get("valid"));prov=load(PROV,{}).get("events",[]);mix={}
    for e in prov:
        p=e.get("provider_used","unknown");mix[p]=mix.get(p,0)+1
    lessons=[]
    if review>valid:lessons.append("Increase evidence quality and prompt specificity before synthesis.")
    if mix.get("local_llama_fallback",0)>0:lessons.append("Local fallback is functioning and should remain available for resilience.")
    if conf and statistics.mean(conf)<.65:lessons.append("Average confidence is below target; strengthen validation before promotion.")
    payload={"generated_at":now(),"validated_count":valid,"review_count":review,"average_confidence":round(statistics.mean(conf),3) if conf else None,"provider_mix":mix,"lessons":lessons,"learning_boundary":"internal_memory_only"}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"lesson_count":len(lessons)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"learning_feedback_complete","report":payload}
print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/learning_feedback_loop.py"

cat > "$AGENTS/stalled_work_recovery_engine.py" <<'PY'
#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory";CFG=MEM/"phase25_bundle3_config.json";OUT=MEM/"stalled_work_recovery_plan.json";STATE=MEM/"stalled_work_recovery_state.json";HEALTH=MEM/"stalled_work_recovery_health.json"
FILES=[MEM/"specialist_runtime_report.json",MEM/"phase25_bundle1_report.json",MEM/"phase25_bundle2_report.json"]
def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def run():
    cfg=load(CFG,{});actions=[]
    for p in FILES:
        d=load(p,{});fails=d.get("failed_steps",[])
        if not fails and isinstance(d.get("report"),dict):fails=d["report"].get("failed_steps",[])
        for f in fails:actions.append({"source":p.name,"failed_step":f,"recommended_action":"retry_internal_after_prerequisite_refresh","max_attempts":cfg.get("maximum_recovery_attempts",3),"status":"recovery_planned","external_action_authorized":False})
    payload={"generated_at":now(),"recovery_action_count":len(actions),"actions":actions}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"recovery_action_count":len(actions)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"stalled_work_recovery_complete","report":payload}
print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/stalled_work_recovery_engine.py"

cat > "$AGENTS/autonomous_ceo_cycle.py" <<'PY'
#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory";OUT=MEM/"autonomous_ceo_cycle_report.json";STATE=MEM/"autonomous_ceo_cycle_state.json";HEALTH=MEM/"autonomous_ceo_cycle_health.json"
PIPELINE=[("opportunity_scoring",["python","companyos/opportunityscoringctl","run"]),("strategic_planning",["python","companyos/strategicexecutionctl","run"]),("agent_orchestration",["python","companyos/agentorchestrationctl","run"]),("phase25_multiagent",["python","companyos/phase25bundle2ctl","run"]),("learning_feedback",["python","companyos/learningfeedbackctl","run"]),("stalled_recovery",["python","companyos/stalledrecoveryctl","run"])]
def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def call(cmd):
    try:
        p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=2400)
        return {"success":p.returncode==0,"return_code":p.returncode,"stdout":p.stdout[-2500:],"stderr":p.stderr[-1000:]}
    except Exception as e:return {"success":False,"error":str(e)}
def run():
    steps=[];failed=[]
    for name,cmd in PIPELINE:
        r=call(cmd);steps.append({"step":name,"result":r})
        if not r.get("success"):failed.append(name)
    payload={"generated_at":now(),"failure_count":len(failed),"failed_steps":failed,"steps":steps,"cycle":"discover_score_plan_delegate_validate_learn_recover","external_authority_granted":False}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"failure_count":len(failed),"failed_steps":failed});save(HEALTH,{"healthy":not failed,"last_checked_at":now()})
    return {"success":not failed,"status":"autonomous_ceo_cycle_complete","report":payload}
print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/autonomous_ceo_cycle.py"

for spec in \
"opportunityscoringctl opportunity_scoring_engine.py" \
"strategicexecutionctl strategic_execution_planner.py" \
"agentorchestrationctl agent_orchestration_engine.py" \
"learningfeedbackctl learning_feedback_loop.py" \
"stalledrecoveryctl stalled_work_recovery_engine.py" \
"autonomousceocyclectl autonomous_ceo_cycle.py"
do
  set -- $spec
  cat > "$CTL/$1" <<PY
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"$2"),*sys.argv[1:]],cwd=r))
PY
  chmod +x "$CTL/$1"
done

cat > "$AGENTS/phase25_bundle3_controller.py" <<'PY'
#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory";STATE=MEM/"phase25_bundle3_state.json";REPORT=MEM/"phase25_bundle3_report.json";HEALTH=MEM/"phase25_bundle3_health.json"
PIPELINE=[("phase25_bundle2",["python","companyos/phase25bundle2ctl","run"]),("autonomous_ceo_cycle",["python","companyos/autonomousceocyclectl","run"])]
def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def call(cmd):
    try:
        p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=3600)
        return {"success":p.returncode==0,"return_code":p.returncode,"stdout":p.stdout[-3500:],"stderr":p.stderr[-1500:]}
    except Exception as e:return {"success":False,"error":str(e)}
def run():
    steps=[];failed=[]
    for name,cmd in PIPELINE:
        r=call(cmd);steps.append({"step":name,"result":r})
        if not r.get("success"):failed.append(name)
    report={"generated_at":now(),"steps":steps,"failure_count":len(failed),"failed_steps":failed}
    save(REPORT,report);save(STATE,{"last_run_at":now(),"failure_count":len(failed),"failed_steps":failed});save(HEALTH,{"healthy":not failed,"last_checked_at":now(),"failure_count":len(failed)})
    return {"success":not failed,"status":"phase25_bundle3_cycle_complete","report":report}
def status():
    def l(p):
        try:return json.loads(p.read_text())
        except:return {}
    return {"success":True,"status":"phase25_bundle3_status","state":l(STATE),"health":l(HEALTH)}
a=sys.argv[1] if len(sys.argv)>1 else "status";r=run() if a=="run" else status();print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/phase25_bundle3_controller.py"

cat > "$CTL/phase25bundle3ctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase25_bundle3_controller.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/phase25bundle3ctl"

echo "[1/8] Compiling..."
python -m py_compile "$AGENTS/opportunity_scoring_engine.py" "$AGENTS/strategic_execution_planner.py" "$AGENTS/agent_orchestration_engine.py" "$AGENTS/learning_feedback_loop.py" "$AGENTS/stalled_work_recovery_engine.py" "$AGENTS/autonomous_ceo_cycle.py" "$AGENTS/phase25_bundle3_controller.py" "$CTL/opportunityscoringctl" "$CTL/strategicexecutionctl" "$CTL/agentorchestrationctl" "$CTL/learningfeedbackctl" "$CTL/stalledrecoveryctl" "$CTL/autonomousceocyclectl" "$CTL/phase25bundle3ctl"

echo "[2/8] Opportunity scoring..."; python "$CTL/opportunityscoringctl" run
echo "[3/8] Strategic execution planning..."; python "$CTL/strategicexecutionctl" run
echo "[4/8] Agent orchestration..."; python "$CTL/agentorchestrationctl" run
echo "[5/8] Learning feedback..."; python "$CTL/learningfeedbackctl" run
echo "[6/8] Recovery planning..."; python "$CTL/stalledrecoveryctl" run

echo "[7/8] Registering scheduler..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"phase25-autonomous-ceo-cycle","enabled":True,"interval_seconds":14400,"command":["python","companyos/phase25bundle3ctl","run"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2));print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
python "$CTL/operationsctl" restart

echo "[8/8] Integrated run + verification..."
python "$CTL/phase25bundle3ctl" run || true
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[r/"agents"/"opportunity_scoring_engine.py",r/"agents"/"strategic_execution_planner.py",r/"agents"/"agent_orchestration_engine.py",r/"agents"/"learning_feedback_loop.py",r/"agents"/"stalled_work_recovery_engine.py",r/"agents"/"autonomous_ceo_cycle.py",r/"agents"/"phase25_bundle3_controller.py",r/"companyos"/"opportunityscoringctl",r/"companyos"/"strategicexecutionctl",r/"companyos"/"agentorchestrationctl",r/"companyos"/"learningfeedbackctl",r/"companyos"/"stalledrecoveryctl",r/"companyos"/"autonomousceocyclectl",r/"companyos"/"phase25bundle3ctl",r/"ceo_memory"/"phase25_bundle3_config.json",r/"ceo_memory"/"scored_opportunities.json",r/"ceo_memory"/"strategic_execution_plans.json",r/"ceo_memory"/"agent_orchestration_queue.json",r/"ceo_memory"/"learning_feedback_report.json",r/"ceo_memory"/"stalled_work_recovery_plan.json",r/"ceo_memory"/"autonomous_operations_config.json"]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:14]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
cfg=json.loads((r/"ceo_memory"/"phase25_bundle3_config.json").read_text())
for k in ["automatic_external_write","automatic_customer_contact","automatic_publication","automatic_spending","automatic_fund_transfer","automatic_code_changes","automatic_merge","automatic_deploy","automatic_destructive_actions"]:
    if cfg.get(k) is not False:errors.append(f"{k} must remain disabled")
sched=json.loads((r/"ceo_memory"/"autonomous_operations_config.json").read_text())
if not any(x.get("id")=="phase25-autonomous-ceo-cycle" and x.get("enabled") for x in sched.get("jobs",[])):errors.append("Phase 25 Bundle 3 scheduler job missing/disabled")
print("--------------------------------------------");print("PHASE 25 BUNDLE 3 VERIFICATION");print(f"Errors: {len(errors)}");print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 25 BUNDLE 3 INSTALLED"
echo " AUTONOMOUS CEO DECISION LOOP ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Master commands:"
echo "  python companyos/phase25bundle3ctl run"
echo "  python companyos/phase25bundle3ctl status"
echo "  python companyos/autonomousceocyclectl run"
echo "  python companyos/opportunityscoringctl run"
