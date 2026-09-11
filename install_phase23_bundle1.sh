#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase23_bundle1_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " PHASE 23 BUNDLE 1 - ADAPTIVE BUSINESS INTELLIGENCE CORE"
echo "============================================================"

# Backup files this bundle may replace.
for f in \
  "$AGENTS/persistent_memory_engine.py" \
  "$AGENTS/business_signal_engine.py" \
  "$AGENTS/opportunity_generation_engine.py" \
  "$AGENTS/performance_scoring_engine.py" \
  "$AGENTS/self_improvement_proposal_engine.py" \
  "$AGENTS/executive_dashboard_engine.py" \
  "$AGENTS/phase23_controller.py" \
  "$CTL/memoryctl" \
  "$CTL/businesssignalctl" \
  "$CTL/opportunitygenctl" \
  "$CTL/performancecorectl" \
  "$CTL/improvementproposalctl" \
  "$CTL/executivedashboardctl" \
  "$CTL/phase23ctl"
do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/phase23_config.json" <<'JSON'
{
  "enabled": true,
  "memory_max_events": 5000,
  "maximum_generated_opportunities": 20,
  "minimum_opportunity_score": 45,
  "maximum_improvement_proposals": 20,
  "automatic_internal_memory": true,
  "automatic_internal_analysis": true,
  "automatic_internal_opportunity_generation": true,
  "automatic_internal_improvement_proposals": true,
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

# ------------------------------------------------------------
# Persistent memory engine
# ------------------------------------------------------------
cat > "$AGENTS/persistent_memory_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json, sys, hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase23_config.json"
STORE=MEM/"persistent_business_memory.json"
STATE=MEM/"persistent_memory_state.json"
HEALTH=MEM/"persistent_memory_health.json"

SOURCES=[
  "autonomy_core_report.json",
  "validated_insights.json",
  "ceo_decision_candidates.json",
  "governed_ceo_decisions.json",
  "opportunity_discovery_results.json",
  "portfolio_performance_report.json",
  "business_forecast.json",
  "outcome_tracker_report.json",
  "specialist_runtime_results.json"
]

def now(): return datetime.now(timezone.utc).isoformat()
def load(p:Path,d:Any):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p:Path,d:Any):
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(d,indent=2),encoding="utf-8"); t.replace(p)
def digest(x:Any)->str:
    return hashlib.sha256(json.dumps(x,sort_keys=True,default=str).encode()).hexdigest()

def ingest():
    cfg=load(CFG,{})
    store=load(STORE,{"events":[]})
    events=store.setdefault("events",[])
    known={e.get("fingerprint") for e in events}
    added=[]
    for name in SOURCES:
        p=MEM/name
        if not p.exists(): continue
        data=load(p,None)
        if data is None: continue
        fp=digest({"source":name,"data":data})
        if fp in known: continue
        event={"memory_id":fp[:20],"fingerprint":fp,"source":name,"captured_at":now(),"data":data}
        events.append(event); added.append(event); known.add(fp)
    max_events=int(cfg.get("memory_max_events",5000))
    if len(events)>max_events: events[:]=events[-max_events:]
    store["updated_at"]=now(); store["event_count"]=len(events)
    save(STORE,store)
    save(STATE,{"last_ingest_at":now(),"added_count":len(added),"event_count":len(events)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"event_count":len(events)})
    return {"success":True,"status":"persistent_memory_ingest_complete","added_count":len(added),"event_count":len(events)}

def status():
    return {"success":True,"status":"persistent_memory_status",
      "state":load(STATE,{}),"health":load(HEALTH,{}),
      "event_count":load(STORE,{}).get("event_count",0)}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=ingest() if a=="ingest" else status() if a=="status" else {"success":False,"allowed":["ingest","status"]}
print(json.dumps(r,indent=2)); raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/persistent_memory_engine.py"

cat > "$CTL/memoryctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"persistent_memory_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/memoryctl"

# ------------------------------------------------------------
# Business signal engine
# ------------------------------------------------------------
cat > "$AGENTS/business_signal_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"business_signals.json"; STATE=MEM/"business_signal_state.json"; HEALTH=MEM/"business_signal_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(name,d):
    p=MEM/name
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def run():
    signals=[]
    forecast=load("business_forecast.json",{})
    priorities=load("portfolio_resource_priorities.json",{})
    outcomes=load("outcome_tracker_report.json",{})
    crm=load("crm_state.json",{})
    accounting=load("accounting_state.json",{})

    if forecast:
        signals.append({"type":"forecast","strength":70,"source":"business_forecast","data":forecast})
    for x in priorities.get("candidates",[])[:10]:
        signals.append({"type":"priority_opportunity","strength":float(x.get("resource_readiness_score",50) or 50),"source":"portfolio","data":x})
    if outcomes:
        signals.append({"type":"outcomes","strength":60,"source":"outcome_tracker","data":outcomes})
    if crm:
        signals.append({"type":"crm","strength":55,"source":"crm","data":crm})
    if accounting:
        signals.append({"type":"finance","strength":65,"source":"accounting","data":accounting})

    payload={"generated_at":now(),"signal_count":len(signals),"signals":signals}
    save(OUT,payload); save(STATE,{"last_run_at":now(),"signal_count":len(signals)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"signal_count":len(signals)})
    return {"success":True,"status":"business_signal_generation_complete","report":payload}

def status():
    return {"success":True,"status":"business_signal_status","state":load("business_signal_state.json",{}),
      "health":load("business_signal_health.json",{}),"report":load("business_signals.json",{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=run() if a=="run" else status() if a=="status" else {"success":False,"allowed":["run","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/business_signal_engine.py"

cat > "$CTL/businesssignalctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"business_signal_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/businesssignalctl"

# ------------------------------------------------------------
# Opportunity generation engine
# ------------------------------------------------------------
cat > "$AGENTS/opportunity_generation_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase23_config.json"; SIGNALS=MEM/"business_signals.json"
OUT=MEM/"generated_business_opportunities.json"; STATE=MEM/"opportunity_generation_state.json"; HEALTH=MEM/"opportunity_generation_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def oid(title,source):return hashlib.sha256(f"{title}|{source}".encode()).hexdigest()[:16]

def generate():
    cfg=load(CFG,{})
    rows=load(SIGNALS,{}).get("signals",[])
    out=[]
    for s in rows:
        typ=s.get("type")
        data=s.get("data",{})
        strength=float(s.get("strength",50) or 50)
        title=None; category="general"; reason=""
        if typ=="priority_opportunity":
            title=data.get("title") or "Advance high-priority business opportunity"
            category=data.get("category") or "growth"
            reason="High internal readiness score"
        elif typ=="forecast":
            title="Review forecast-driven growth or risk actions"
            category="strategy"; reason="Forecast signal available"
        elif typ=="finance":
            title="Improve cash flow, margin, or receivable performance"
            category="finance"; reason="Financial signal available"
        elif typ=="crm":
            title="Advance customer pipeline and retention opportunities"
            category="sales"; reason="CRM signal available"
        elif typ=="outcomes":
            title="Scale actions with strongest measured outcomes"
            category="optimization"; reason="Outcome feedback available"
        if not title: continue
        out.append({"id":oid(title,s.get("source")),"title":title,"category":category,
          "score":round(strength,2),"reason":reason,"source":s.get("source"),
          "status":"generated_internal_candidate","generated_at":now()})
    dedup={x["id"]:x for x in out}
    rows=list(dedup.values())
    rows=[x for x in rows if x["score"]>=float(cfg.get("minimum_opportunity_score",45))]
    rows=sorted(rows,key=lambda x:x["score"],reverse=True)[:int(cfg.get("maximum_generated_opportunities",20))]
    payload={"generated_at":now(),"opportunity_count":len(rows),"opportunities":rows}
    save(OUT,payload);save(STATE,{"last_generated_at":now(),"opportunity_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"opportunity_count":len(rows)})
    return {"success":True,"status":"business_opportunity_generation_complete","report":payload}

def status():
    return {"success":True,"status":"business_opportunity_generation_status",
      "state":load(STATE,{}),"health":load(HEALTH,{}),"report":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=generate() if a=="generate" else status() if a=="status" else {"success":False,"allowed":["generate","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/opportunity_generation_engine.py"

cat > "$CTL/opportunitygenctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"opportunity_generation_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/opportunitygenctl"

# ------------------------------------------------------------
# Performance scoring engine
# ------------------------------------------------------------
cat > "$AGENTS/performance_scoring_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"business_performance_scorecard.json"; STATE=MEM/"business_performance_state.json"; HEALTH=MEM/"business_performance_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(name,d):
    try:return json.loads((MEM/name).read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def score():
    autonomy=load("autonomy_core_health.json",{})
    resource=load("resource_monitor_report.json",{})
    portfolio=load("portfolio_performance_report.json",{})
    outcomes=load("outcome_tracker_report.json",{})
    reliability=load("reliability_health.json",{})

    metrics={
      "autonomy_health":100 if autonomy.get("healthy",False) else 50,
      "reliability":float(reliability.get("reliability_score",80) or 80),
      "portfolio_activity":min(100,float(portfolio.get("priority_count",0) or 0)*20+40),
      "outcome_visibility":80 if outcomes else 40,
      "resource_health":100 if resource.get("status") in ("healthy","ok",None) else 60
    }
    overall=round(sum(metrics.values())/len(metrics),2)
    payload={"generated_at":now(),"overall_score":overall,"metrics":metrics,
      "status":"healthy" if overall>=75 else "watch" if overall>=55 else "attention"}
    save(OUT,payload);save(STATE,{"last_scored_at":now(),"overall_score":overall})
    save(HEALTH,{"healthy":overall>=55,"last_checked_at":now(),"overall_score":overall})
    return {"success":True,"status":"business_performance_scoring_complete","scorecard":payload}

def status():
    return {"success":True,"status":"business_performance_status",
      "state":load("business_performance_state.json",{}),"health":load("business_performance_health.json",{}),
      "scorecard":load("business_performance_scorecard.json",{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=score() if a=="score" else status() if a=="status" else {"success":False,"allowed":["score","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/performance_scoring_engine.py"

cat > "$CTL/performancecorectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"performance_scoring_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/performancecorectl"

# ------------------------------------------------------------
# Self-improvement proposal engine
# ------------------------------------------------------------
cat > "$AGENTS/self_improvement_proposal_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase23_config.json"; OUT=MEM/"self_improvement_proposals.json"
STATE=MEM/"self_improvement_proposal_state.json"; HEALTH=MEM/"self_improvement_proposal_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(name,d):
    try:return json.loads((MEM/name).read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def pid(text):return hashlib.sha256(text.encode()).hexdigest()[:16]

def propose():
    cfg=load("phase23_config.json",{})
    perf=load("business_performance_scorecard.json",{})
    autonomy=load("autonomy_core_report.json",{})
    usage=load("api_usage_state.json",{})
    proposals=[]

    if float(perf.get("overall_score",100) or 100)<75:
        proposals.append(("Improve low-scoring business performance dimensions",80,"performance"))
    failed=autonomy.get("failed_steps",[]) or []
    if failed:
        proposals.append((f"Investigate repeated autonomy failures: {', '.join(failed[:5])}",95,"reliability"))
    if int(usage.get("requests",0) or 0)>100:
        proposals.append(("Reduce unnecessary AI calls using stronger deduplication and batching",75,"efficiency"))
    proposals.append(("Review high-value repeated manual workflows for safe internal automation",65,"automation"))
    proposals.append(("Improve specialist prompt quality using measured result confidence and outcomes",70,"ai_quality"))

    rows=[{"id":pid(t),"title":t,"priority":p,"category":c,
      "status":"proposal_only_requires_governed_review","generated_at":now()} for t,p,c in proposals]
    rows=sorted(rows,key=lambda x:x["priority"],reverse=True)[:int(cfg.get("maximum_improvement_proposals",20))]
    payload={"generated_at":now(),"proposal_count":len(rows),"proposals":rows,
      "automatic_code_changes":False,"automatic_merge":False,"automatic_deploy":False}
    save(OUT,payload);save(STATE,{"last_generated_at":now(),"proposal_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"proposal_count":len(rows)})
    return {"success":True,"status":"self_improvement_proposals_complete","report":payload}

def status():
    return {"success":True,"status":"self_improvement_proposal_status",
      "state":load("self_improvement_proposal_state.json",{}),"health":load("self_improvement_proposal_health.json",{}),
      "report":load("self_improvement_proposals.json",{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=propose() if a=="propose" else status() if a=="status" else {"success":False,"allowed":["propose","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/self_improvement_proposal_engine.py"

cat > "$CTL/improvementproposalctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"self_improvement_proposal_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/improvementproposalctl"

# ------------------------------------------------------------
# Executive dashboard engine
# ------------------------------------------------------------
cat > "$AGENTS/executive_dashboard_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"phase23_executive_dashboard.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(name,d):
    try:return json.loads((MEM/name).read_text(encoding="utf-8"))
    except:return d

def build():
    payload={
      "generated_at":now(),
      "autonomy":load("autonomy_core_health.json",{}),
      "performance":load("business_performance_scorecard.json",{}),
      "opportunities":load("generated_business_opportunities.json",{}),
      "improvement_proposals":load("self_improvement_proposals.json",{}),
      "memory":load("persistent_memory_state.json",{}),
      "api_usage":load("api_usage_state.json",{}),
      "specialist_runtime":load("specialist_runtime_health.json",{}),
      "validated_insights":load("validated_insights.json",{}),
      "external_authority":{
        "external_write":False,"customer_contact":False,"publication":False,
        "spending":False,"fund_transfer":False,"code_changes":False,
        "merge":False,"deploy":False,"destructive_actions":False
      }
    }
    OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    return {"success":True,"status":"phase23_executive_dashboard_complete","dashboard":payload}

a=sys.argv[1] if len(sys.argv)>1 else "show"
r=build()
print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/executive_dashboard_engine.py"

cat > "$CTL/executivedashboardctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"executive_dashboard_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/executivedashboardctl"

# ------------------------------------------------------------
# Master Phase 23 controller
# ------------------------------------------------------------
cat > "$AGENTS/phase23_controller.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
STATE=MEM/"phase23_state.json"; REPORT=MEM/"phase23_report.json"; HEALTH=MEM/"phase23_health.json"

PIPELINE=[
 ("autonomy",["python","companyos/autonomyctl","run"]),
 ("memory",["python","companyos/memoryctl","ingest"]),
 ("signals",["python","companyos/businesssignalctl","run"]),
 ("opportunities",["python","companyos/opportunitygenctl","generate"]),
 ("performance",["python","companyos/performancecorectl","score"]),
 ("improvements",["python","companyos/improvementproposalctl","propose"]),
 ("dashboard",["python","companyos/executivedashboardctl","show"])
]

def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def call(cmd):
    try:
        p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=1200)
        return {"success":p.returncode==0,"return_code":p.returncode,"stdout":p.stdout[-3500:],"stderr":p.stderr[-1500:]}
    except Exception as e:return {"success":False,"error":str(e)}

def run():
    steps=[];failed=[]
    for name,cmd in PIPELINE:
        r=call(cmd);steps.append({"step":name,"result":r})
        if not r.get("success"):failed.append(name)
    report={"generated_at":now(),"steps":steps,"failure_count":len(failed),"failed_steps":failed}
    save(REPORT,report);save(STATE,{"last_run_at":now(),"failure_count":len(failed),"failed_steps":failed})
    save(HEALTH,{"healthy":not failed,"last_checked_at":now(),"failure_count":len(failed)})
    return {"success":not failed,"status":"phase23_adaptive_business_intelligence_cycle_complete","report":report}

def status():
    try:s=json.loads(STATE.read_text())
    except:s={}
    try:h=json.loads(HEALTH.read_text())
    except:h={}
    return {"success":True,"status":"phase23_status","state":s,"health":h}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=run() if a=="run" else status() if a=="status" else {"success":False,"allowed":["run","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/phase23_controller.py"

cat > "$CTL/phase23ctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase23_controller.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/phase23ctl"

echo "[1/8] Compiling Phase 23 bundle..."
python -m py_compile \
 "$AGENTS/persistent_memory_engine.py" \
 "$AGENTS/business_signal_engine.py" \
 "$AGENTS/opportunity_generation_engine.py" \
 "$AGENTS/performance_scoring_engine.py" \
 "$AGENTS/self_improvement_proposal_engine.py" \
 "$AGENTS/executive_dashboard_engine.py" \
 "$AGENTS/phase23_controller.py" \
 "$CTL/memoryctl" "$CTL/businesssignalctl" "$CTL/opportunitygenctl" \
 "$CTL/performancecorectl" "$CTL/improvementproposalctl" "$CTL/executivedashboardctl" "$CTL/phase23ctl"

echo "[2/8] Initializing memory..."
python "$CTL/memoryctl" ingest

echo "[3/8] Generating business signals and opportunities..."
python "$CTL/businesssignalctl" run
python "$CTL/opportunitygenctl" generate

echo "[4/8] Scoring performance and generating improvement proposals..."
python "$CTL/performancecorectl" score
python "$CTL/improvementproposalctl" propose

echo "[5/8] Building executive dashboard..."
python "$CTL/executivedashboardctl" show

echo "[6/8] Registering Phase 23 scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"phase23-adaptive-business-intelligence","enabled":True,"interval_seconds":7200,
"command":["python","companyos/phase23ctl","run"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2),encoding="utf-8")
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY

echo "[7/8] Restarting scheduler and running one Phase 23 cycle..."
python "$CTL/operationsctl" restart
python "$CTL/phase23ctl" run || true

echo "[8/8] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[];warnings=[]
req=[
r/"agents"/"persistent_memory_engine.py",r/"agents"/"business_signal_engine.py",
r/"agents"/"opportunity_generation_engine.py",r/"agents"/"performance_scoring_engine.py",
r/"agents"/"self_improvement_proposal_engine.py",r/"agents"/"executive_dashboard_engine.py",
r/"agents"/"phase23_controller.py",r/"companyos"/"memoryctl",r/"companyos"/"businesssignalctl",
r/"companyos"/"opportunitygenctl",r/"companyos"/"performancecorectl",r/"companyos"/"improvementproposalctl",
r/"companyos"/"executivedashboardctl",r/"companyos"/"phase23ctl",
r/"ceo_memory"/"phase23_config.json",r/"ceo_memory"/"persistent_business_memory.json",
r/"ceo_memory"/"business_signals.json",r/"ceo_memory"/"generated_business_opportunities.json",
r/"ceo_memory"/"business_performance_scorecard.json",r/"ceo_memory"/"self_improvement_proposals.json",
r/"ceo_memory"/"phase23_executive_dashboard.json",r/"ceo_memory"/"autonomous_operations_config.json"
]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:14]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
cfg=json.loads((r/"ceo_memory"/"phase23_config.json").read_text())
for k in ["automatic_external_write","automatic_customer_contact","automatic_publication","automatic_spending",
"automatic_fund_transfer","automatic_code_changes","automatic_merge","automatic_deploy","automatic_destructive_actions"]:
    if cfg.get(k) is not False:errors.append(f"{k} must remain disabled")
sched=json.loads((r/"ceo_memory"/"autonomous_operations_config.json").read_text())
if not any(x.get("id")=="phase23-adaptive-business-intelligence" and x.get("enabled") for x in sched.get("jobs",[])):
    errors.append("Phase 23 scheduler job missing/disabled")
print("--------------------------------------------")
print("PHASE 23 BUNDLE 1 VERIFICATION")
print(f"Errors: {len(errors)}")
print(f"Warnings: {len(warnings)}")
for e in errors:print("ERROR:",e)
for w in warnings:print("WARNING:",w)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 23 BUNDLE 1 INSTALLED"
echo " ADAPTIVE BUSINESS INTELLIGENCE CORE ACTIVE"
echo " Errors: 0"
echo "============================================================"
echo
echo "Master commands:"
echo "  python companyos/phase23ctl run"
echo "  python companyos/phase23ctl status"
echo "  python companyos/executivedashboardctl show"
echo
echo "Bundle includes:"
echo "  - Persistent business memory"
echo "  - Business signal synthesis"
echo "  - Internal opportunity generation"
echo "  - Business performance scoring"
echo "  - Self-improvement proposals"
echo "  - Executive dashboard"
echo "  - Master Phase 23 cycle"
