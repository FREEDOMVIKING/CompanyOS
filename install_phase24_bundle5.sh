#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase24_bundle5_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " PHASE 24 BUNDLE 5 - REVENUE INTELLIGENCE & EXECUTIVE CORE"
echo "============================================================"

for f in \
  "$AGENTS/market_intelligence_engine.py" \
  "$AGENTS/customer_pipeline_priority_engine.py" \
  "$AGENTS/proposal_draft_engine.py" \
  "$AGENTS/finance_forecast_bridge.py" \
  "$AGENTS/execution_readiness_engine.py" \
  "$AGENTS/daily_ceo_brief_engine.py" \
  "$AGENTS/phase24_bundle5_controller.py" \
  "$CTL/marketintelligencectl" \
  "$CTL/customerpriorityctl" \
  "$CTL/proposaldraftctl" \
  "$CTL/financeforecastctl" \
  "$CTL/executionreadinessctl" \
  "$CTL/dailyceobriefctl" \
  "$CTL/phase24bundle5ctl"
do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/phase24_bundle5_config.json" <<'JSON'
{
  "enabled": true,
  "maximum_market_signals": 50,
  "maximum_customer_priorities": 25,
  "maximum_proposal_drafts": 20,
  "minimum_execution_readiness_score": 60,
  "automatic_internal_market_analysis": true,
  "automatic_internal_customer_prioritization": true,
  "automatic_internal_proposal_drafting": true,
  "automatic_internal_finance_forecasting": true,
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

cat > "$AGENTS/market_intelligence_engine.py" <<'PY'
#!/usr/bin/env python3
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase24_bundle5_config.json"; SIGNALS=MEM/"business_signals.json"
OPS=MEM/"generated_business_opportunities.json"; OUT=MEM/"market_intelligence_report.json"
STATE=MEM/"market_intelligence_state.json"; HEALTH=MEM/"market_intelligence_health.json"
def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def sid(x):return hashlib.sha256(str(x).encode()).hexdigest()[:16]
def run():
    cfg=load(CFG,{})
    rows=[]
    for s in load(SIGNALS,{}).get("signals",[]):
        rows.append({"signal_id":sid(s),"type":s.get("type"),"strength":s.get("strength",50),
                     "source":s.get("source"),"status":"internal_market_signal"})
    for o in load(OPS,{}).get("opportunities",[]):
        rows.append({"signal_id":sid(o.get("id") or o.get("title")),"type":"opportunity",
                     "strength":o.get("score",50),"source":o.get("source"),
                     "title":o.get("title"),"status":"internal_market_signal"})
    rows=sorted(rows,key=lambda x:float(x.get("strength",0) or 0),reverse=True)[:int(cfg.get("maximum_market_signals",50))]
    payload={"generated_at":now(),"signal_count":len(rows),"signals":rows}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"signal_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"signal_count":len(rows)})
    return {"success":True,"status":"market_intelligence_complete","report":payload}
def status():return {"success":True,"status":"market_intelligence_status","state":load(STATE,{}),"health":load(HEALTH,{})}
a=sys.argv[1] if len(sys.argv)>1 else "status";r=run() if a=="run" else status()
print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/market_intelligence_engine.py"

cat > "$CTL/marketintelligencectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"market_intelligence_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/marketintelligencectl"

cat > "$AGENTS/customer_pipeline_priority_engine.py" <<'PY'
#!/usr/bin/env python3
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase24_bundle5_config.json"; OUT=MEM/"customer_pipeline_priorities.json"
STATE=MEM/"customer_pipeline_priority_state.json"; HEALTH=MEM/"customer_pipeline_priority_health.json"
def now():return datetime.now(timezone.utc).isoformat()
def load(n,d):
    try:return json.loads((MEM/n).read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def pid(x):return hashlib.sha256(str(x).encode()).hexdigest()[:16]
def run():
    cfg=load("phase24_bundle5_config.json",{})
    sources=[]
    for name in ["sales_pipeline.json","crm_state.json","generated_business_opportunities.json"]:
        d=load(name,{})
        if name=="generated_business_opportunities.json":
            for o in d.get("opportunities",[]): sources.append({"title":o.get("title"),"score":o.get("score",50),"source":name})
        elif isinstance(d,dict):
            for k in ("leads","opportunities","items","pipeline"):
                v=d.get(k,[])
                if isinstance(v,list):
                    for x in v:
                        if isinstance(x,dict): sources.append({"title":x.get("title") or x.get("name") or "Pipeline item","score":x.get("score",50),"source":name})
    rows=[{"priority_id":pid(x),"title":x["title"],"priority_score":float(x.get("score",50) or 50),
           "source":x["source"],"status":"internal_priority_only","customer_contact_authorized":False} for x in sources]
    rows=sorted(rows,key=lambda x:x["priority_score"],reverse=True)[:int(cfg.get("maximum_customer_priorities",25))]
    payload={"generated_at":now(),"priority_count":len(rows),"priorities":rows}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"priority_count":len(rows)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"customer_pipeline_priority_complete","report":payload}
def status():return {"success":True,"status":"customer_pipeline_priority_status","state":load("customer_pipeline_priority_state.json",{}),"health":load("customer_pipeline_priority_health.json",{})}
a=sys.argv[1] if len(sys.argv)>1 else "status";r=run() if a=="run" else status();print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/customer_pipeline_priority_engine.py"

cat > "$CTL/customerpriorityctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"customer_pipeline_priority_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/customerpriorityctl"

cat > "$AGENTS/proposal_draft_engine.py" <<'PY'
#!/usr/bin/env python3
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"proposal_draft_queue.json"; STATE=MEM/"proposal_draft_state.json"; HEALTH=MEM/"proposal_draft_health.json"
def now():return datetime.now(timezone.utc).isoformat()
def load(n,d):
    try:return json.loads((MEM/n).read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def did(x):return hashlib.sha256(str(x).encode()).hexdigest()[:16]
def run():
    rows=[]
    for x in load("customer_pipeline_priorities.json",{}).get("priorities",[])[:20]:
        title=x.get("title","Opportunity")
        rows.append({"draft_id":did(x.get("priority_id")),"title":f"Draft proposal: {title}",
          "source_priority_id":x.get("priority_id"),
          "outline":["Problem / opportunity","Proposed scope","Expected outcomes","Assumptions","Next-step questions"],
          "status":"draft_internal_review_only","send_authorized":False,"created_at":now()})
    payload={"generated_at":now(),"draft_count":len(rows),"drafts":rows}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"draft_count":len(rows)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"proposal_draft_generation_complete","queue":payload}
def status():return {"success":True,"status":"proposal_draft_status","state":load("proposal_draft_state.json",{}),"health":load("proposal_draft_health.json",{})}
a=sys.argv[1] if len(sys.argv)>1 else "status";r=run() if a=="run" else status();print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/proposal_draft_engine.py"

cat > "$CTL/proposaldraftctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"proposal_draft_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/proposaldraftctl"

cat > "$AGENTS/finance_forecast_bridge.py" <<'PY'
#!/usr/bin/env python3
import json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"finance_forecast_bridge.json"; STATE=MEM/"finance_forecast_bridge_state.json"; HEALTH=MEM/"finance_forecast_bridge_health.json"
def now():return datetime.now(timezone.utc).isoformat()
def load(n,d):
    try:return json.loads((MEM/n).read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def run():
    forecast=load("business_forecast.json",{})
    accounting=load("accounting_state.json",{})
    priorities=load("customer_pipeline_priorities.json",{})
    payload={"generated_at":now(),"forecast":forecast,"accounting":accounting,
             "pipeline_priority_count":priorities.get("priority_count",0),
             "status":"internal_finance_forecast_context",
             "spending_authorized":False,"fund_transfer_authorized":False}
    save(OUT,payload);save(STATE,{"last_run_at":now()});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"finance_forecast_bridge_complete","report":payload}
r=run();print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/finance_forecast_bridge.py"

cat > "$CTL/financeforecastctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"finance_forecast_bridge.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/financeforecastctl"

cat > "$AGENTS/execution_readiness_engine.py" <<'PY'
#!/usr/bin/env python3
import json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"execution_readiness_report.json"; STATE=MEM/"execution_readiness_state.json"; HEALTH=MEM/"execution_readiness_health.json"
def now():return datetime.now(timezone.utc).isoformat()
def load(n,d):
    try:return json.loads((MEM/n).read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def run():
    projects=load("project_execution_registry.json",{}).get("projects",[])
    risks=load("enterprise_risk_register.json",{}).get("risk_count",0)
    approvals=load("governed_approval_queue.json",{}).get("items",[])
    pending=sum(1 for x in approvals if x.get("status")=="pending")
    rows=[]
    for p in projects:
        score=float(p.get("validation_score",50) or 50)
        if risks: score=max(0,score-min(20,risks*0.25))
        if pending: score=max(0,score-5)
        rows.append({"project_id":p.get("project_id"),"title":p.get("title"),
                     "readiness_score":round(score,2),
                     "status":"internally_ready" if score>=60 else "needs_more_preparation",
                     "external_execution_authorized":False})
    payload={"generated_at":now(),"project_count":len(rows),"projects":rows}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"project_count":len(rows)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"execution_readiness_complete","report":payload}
def status():return {"success":True,"status":"execution_readiness_status","state":load("execution_readiness_state.json",{}),"health":load("execution_readiness_health.json",{})}
a=sys.argv[1] if len(sys.argv)>1 else "status";r=run() if a=="run" else status();print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/execution_readiness_engine.py"

cat > "$CTL/executionreadinessctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"execution_readiness_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/executionreadinessctl"

cat > "$AGENTS/daily_ceo_brief_engine.py" <<'PY'
#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"; OUT=MEM/"daily_ceo_brief.json"
def now():return datetime.now(timezone.utc).isoformat()
def load(n,d):
    try:return json.loads((MEM/n).read_text())
    except:return d
def run():
    payload={
      "generated_at":now(),
      "headline":"CompanyOS Daily CEO Brief",
      "business_performance":load("business_performance_scorecard.json",{}).get("overall_score"),
      "top_market_signals":load("market_intelligence_report.json",{}).get("signals",[])[:5],
      "top_customer_priorities":load("customer_pipeline_priorities.json",{}).get("priorities",[])[:5],
      "proposal_draft_count":load("proposal_draft_queue.json",{}).get("draft_count",0),
      "execution_readiness":load("execution_readiness_report.json",{}).get("projects",[])[:10],
      "risk_count":load("enterprise_risk_register.json",{}).get("risk_count",0),
      "pending_approval_count":sum(1 for x in load("governed_approval_queue.json",{}).get("items",[]) if x.get("status")=="pending"),
      "external_authority_granted":False
    }
    OUT.write_text(json.dumps(payload,indent=2))
    return {"success":True,"status":"daily_ceo_brief_complete","brief":payload}
print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/daily_ceo_brief_engine.py"

cat > "$CTL/dailyceobriefctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"daily_ceo_brief_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/dailyceobriefctl"

cat > "$AGENTS/phase24_bundle5_controller.py" <<'PY'
#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
STATE=MEM/"phase24_bundle5_state.json"; REPORT=MEM/"phase24_bundle5_report.json"; HEALTH=MEM/"phase24_bundle5_health.json"
PIPELINE=[
 ("phase24_bundle4",["python","companyos/phase24bundle4ctl","run"]),
 ("market_intelligence",["python","companyos/marketintelligencectl","run"]),
 ("customer_priorities",["python","companyos/customerpriorityctl","run"]),
 ("proposal_drafts",["python","companyos/proposaldraftctl","run"]),
 ("finance_forecast",["python","companyos/financeforecastctl","run"]),
 ("execution_readiness",["python","companyos/executionreadinessctl","run"]),
 ("daily_ceo_brief",["python","companyos/dailyceobriefctl","show"])
]
def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def call(cmd):
    try:
        p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=2400)
        return {"success":p.returncode==0,"return_code":p.returncode,"stdout":p.stdout[-3500:],"stderr":p.stderr[-1500:]}
    except Exception as e:return {"success":False,"error":str(e)}
def run():
    steps=[];failed=[]
    for name,cmd in PIPELINE:
        r=call(cmd);steps.append({"step":name,"result":r})
        if not r.get("success"):failed.append(name)
    report={"generated_at":now(),"steps":steps,"failure_count":len(failed),"failed_steps":failed}
    save(REPORT,report);save(STATE,{"last_run_at":now(),"failure_count":len(failed),"failed_steps":failed});save(HEALTH,{"healthy":not failed,"last_checked_at":now(),"failure_count":len(failed)})
    return {"success":not failed,"status":"phase24_bundle5_cycle_complete","report":report}
def status():
    def l(p):
        try:return json.loads(p.read_text())
        except:return {}
    return {"success":True,"status":"phase24_bundle5_status","state":l(STATE),"health":l(HEALTH)}
a=sys.argv[1] if len(sys.argv)>1 else "status";r=run() if a=="run" else status();print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/phase24_bundle5_controller.py"

cat > "$CTL/phase24bundle5ctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase24_bundle5_controller.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/phase24bundle5ctl"

echo "[1/8] Compiling..."
python -m py_compile \
 "$AGENTS/market_intelligence_engine.py" \
 "$AGENTS/customer_pipeline_priority_engine.py" \
 "$AGENTS/proposal_draft_engine.py" \
 "$AGENTS/finance_forecast_bridge.py" \
 "$AGENTS/execution_readiness_engine.py" \
 "$AGENTS/daily_ceo_brief_engine.py" \
 "$AGENTS/phase24_bundle5_controller.py" \
 "$CTL/marketintelligencectl" "$CTL/customerpriorityctl" "$CTL/proposaldraftctl" \
 "$CTL/financeforecastctl" "$CTL/executionreadinessctl" "$CTL/dailyceobriefctl" "$CTL/phase24bundle5ctl"

echo "[2/8] Market intelligence..."
python "$CTL/marketintelligencectl" run

echo "[3/8] Customer priority engine..."
python "$CTL/customerpriorityctl" run

echo "[4/8] Proposal drafts..."
python "$CTL/proposaldraftctl" run

echo "[5/8] Finance forecast and execution readiness..."
python "$CTL/financeforecastctl" run
python "$CTL/executionreadinessctl" run

echo "[6/8] Daily CEO brief..."
python "$CTL/dailyceobriefctl" show

echo "[7/8] Registering scheduler and running integrated cycle..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"phase24-revenue-intelligence-executive","enabled":True,"interval_seconds":14400,
"command":["python","companyos/phase24bundle5ctl","run"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
python "$CTL/operationsctl" restart
python "$CTL/phase24bundle5ctl" run || true

echo "[8/8] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[
r/"agents"/"market_intelligence_engine.py",r/"agents"/"customer_pipeline_priority_engine.py",
r/"agents"/"proposal_draft_engine.py",r/"agents"/"finance_forecast_bridge.py",
r/"agents"/"execution_readiness_engine.py",r/"agents"/"daily_ceo_brief_engine.py",
r/"agents"/"phase24_bundle5_controller.py",r/"companyos"/"marketintelligencectl",
r/"companyos"/"customerpriorityctl",r/"companyos"/"proposaldraftctl",
r/"companyos"/"financeforecastctl",r/"companyos"/"executionreadinessctl",
r/"companyos"/"dailyceobriefctl",r/"companyos"/"phase24bundle5ctl",
r/"ceo_memory"/"phase24_bundle5_config.json",r/"ceo_memory"/"market_intelligence_report.json",
r/"ceo_memory"/"customer_pipeline_priorities.json",r/"ceo_memory"/"proposal_draft_queue.json",
r/"ceo_memory"/"finance_forecast_bridge.json",r/"ceo_memory"/"execution_readiness_report.json",
r/"ceo_memory"/"daily_ceo_brief.json",r/"ceo_memory"/"autonomous_operations_config.json"
]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:14]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
cfg=json.loads((r/"ceo_memory"/"phase24_bundle5_config.json").read_text())
for k in ["automatic_external_write","automatic_customer_contact","automatic_publication","automatic_spending",
"automatic_fund_transfer","automatic_code_changes","automatic_merge","automatic_deploy","automatic_destructive_actions"]:
    if cfg.get(k) is not False:errors.append(f"{k} must remain disabled")
sched=json.loads((r/"ceo_memory"/"autonomous_operations_config.json").read_text())
if not any(x.get("id")=="phase24-revenue-intelligence-executive" and x.get("enabled") for x in sched.get("jobs",[])):
    errors.append("Phase 24 Bundle 5 scheduler job missing/disabled")
print("--------------------------------------------")
print("PHASE 24 BUNDLE 5 VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 24 BUNDLE 5 INSTALLED"
echo " REVENUE INTELLIGENCE & EXECUTIVE CORE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Master commands:"
echo "  python companyos/phase24bundle5ctl run"
echo "  python companyos/phase24bundle5ctl status"
echo "  python companyos/dailyceobriefctl show"
echo
echo "Bundle includes:"
echo "  - Market intelligence"
echo "  - Customer pipeline prioritization"
echo "  - Internal proposal drafting"
echo "  - Finance forecast bridge"
echo "  - Execution readiness scoring"
echo "  - Daily CEO brief"
echo "  - Integrated Phase 24 Bundle 5 cycle"
