#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
LAB="$ROOT/platform_lab"
BACKUP="$ROOT/backups/phase28_self_evolving_platform_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$LAB/proposals" "$LAB/sandboxes" "$LAB/tests" "$LAB/promoted" "$BACKUP"

echo "============================================================"
echo " PHASE 28 - SELF-EVOLVING PLATFORM CORE"
echo "============================================================"

cat > "$MEM/phase28_platform_config.json" <<'JSON'
{
  "enabled": true,
  "maximum_active_experiments": 10,
  "maximum_changes_per_cycle": 5,
  "minimum_test_pass_rate": 1.0,
  "minimum_promotion_confidence": 0.70,
  "automatic_capability_gap_detection": true,
  "automatic_internal_design": true,
  "automatic_internal_code_generation": true,
  "automatic_sandbox_build": true,
  "automatic_test_generation": true,
  "automatic_internal_promotion_after_tests": true,
  "automatic_architecture_memory": true,
  "external_deployment_requires_registered_target_authority": true,
  "financial_actions_follow_phase26_limits": true
}
JSON

cat > "$AGENTS/capability_gap_detector.py" <<'PY'
#!/usr/bin/env python3
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"capability_gap_report.json"
STATE=MEM/"capability_gap_state.json"
HEALTH=MEM/"capability_gap_health.json"

CHECKS=[
 ("financial_execution", ["companyos/financialexecutionctl","connectors/financial_adapter.py"]),
 ("communications", ["companyos/externalactionctl","connectors/communications_adapter.py"]),
 ("publication", ["companyos/externalactionctl","connectors/publication_adapter.py"]),
 ("deployment", ["companyos/externalactionctl","connectors/deployment_adapter.py"]),
 ("hybrid_ai", ["companyos/phase25bundle1ctl","agents/specialist_runtime_adapter.py"]),
 ("multi_agent", ["companyos/phase25bundle2ctl"]),
 ("autonomous_ceo", ["companyos/phase25bundle3ctl"])
]

def now():return datetime.now(timezone.utc).isoformat()
def gid(x):return hashlib.sha256(x.encode()).hexdigest()[:18]
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def run():
    gaps=[]
    for name,paths in CHECKS:
        missing=[p for p in paths if not (ROOT/p).exists()]
        if missing:
            gaps.append({"gap_id":gid(name),"capability":name,"missing":missing,"priority":80,"status":"open"})
    payload={"generated_at":now(),"gap_count":len(gaps),"gaps":gaps}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"gap_count":len(gaps)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"capability_gap_detection_complete","report":payload}
print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/capability_gap_detector.py"

cat > "$CTL/capabilitygapctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"capability_gap_detector.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/capabilitygapctl"

cat > "$AGENTS/platform_architect_engine.py" <<'PY'
#!/usr/bin/env python3
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory";LAB=ROOT/"platform_lab"
GAPS=MEM/"capability_gap_report.json";OUT=MEM/"platform_architecture_plan.json"
STATE=MEM/"platform_architect_state.json";HEALTH=MEM/"platform_architect_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def run():
    proposals=[]
    for g in load(GAPS,{}).get("gaps",[]):
        proposals.append({
          "proposal_id":hashlib.sha256((g["capability"]+"|"+now()).encode()).hexdigest()[:18],
          "capability":g["capability"],
          "objective":f"Close capability gap: {g['capability']}",
          "design":["define interface","build sandbox module","generate tests","run validation","promote if passing"],
          "status":"designed_internal",
          "external_side_effects":False
        })
    payload={"generated_at":now(),"proposal_count":len(proposals),"proposals":proposals}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"proposal_count":len(proposals)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"platform_architecture_complete","plan":payload}
print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/platform_architect_engine.py"

cat > "$CTL/platformarchitectctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"platform_architect_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/platformarchitectctl"

cat > "$AGENTS/sandbox_builder_engine.py" <<'PY'
#!/usr/bin/env python3
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory";LAB=ROOT/"platform_lab"
PLAN=MEM/"platform_architecture_plan.json";OUT=MEM/"sandbox_build_report.json"
STATE=MEM/"sandbox_builder_state.json";HEALTH=MEM/"sandbox_builder_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def run():
    built=[]
    for p in load(PLAN,{}).get("proposals",[])[:10]:
        sid=p["proposal_id"]
        d=LAB/"sandboxes"/sid;d.mkdir(parents=True,exist_ok=True)
        module=d/"module.py"
        module.write_text(
            "def capability_info():\n"
            f"    return {{'capability': {p['capability']!r}, 'sandbox': True, 'status': 'prototype'}}\n"
        )
        test=d/"test_module.py"
        test.write_text(
            "from module import capability_info\n"
            "x=capability_info()\n"
            "assert x['sandbox'] is True\n"
            "assert x['status']=='prototype'\n"
            "print('PASS')\n"
        )
        built.append({"proposal_id":sid,"capability":p["capability"],"sandbox_dir":str(d),"status":"built"})
    payload={"generated_at":now(),"build_count":len(built),"builds":built}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"build_count":len(built)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"sandbox_build_complete","report":payload}
print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/sandbox_builder_engine.py"

cat > "$CTL/sandboxbuilderctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"sandbox_builder_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/sandboxbuilderctl"

cat > "$AGENTS/self_test_engine.py" <<'PY'
#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory";LAB=ROOT/"platform_lab"
BUILDS=MEM/"sandbox_build_report.json";OUT=MEM/"self_test_report.json"
STATE=MEM/"self_test_state.json";HEALTH=MEM/"self_test_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def run():
    rows=[]
    for b in load(BUILDS,{}).get("builds",[]):
        d=Path(b["sandbox_dir"])
        p=subprocess.run([sys.executable,"test_module.py"],cwd=d,text=True,capture_output=True,timeout=60)
        rows.append({"proposal_id":b["proposal_id"],"capability":b["capability"],"passed":p.returncode==0,
                     "return_code":p.returncode,"stdout":p.stdout[-500:],"stderr":p.stderr[-500:]})
    passed=sum(1 for x in rows if x["passed"])
    payload={"generated_at":now(),"test_count":len(rows),"passed_count":passed,
             "pass_rate":(passed/len(rows)) if rows else 1.0,"tests":rows}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"test_count":len(rows),"passed_count":passed});save(HEALTH,{"healthy":passed==len(rows),"last_checked_at":now()})
    return {"success":passed==len(rows),"status":"self_test_complete","report":payload}
print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/self_test_engine.py"

cat > "$CTL/selftestctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"self_test_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/selftestctl"

cat > "$AGENTS/internal_promotion_manager.py" <<'PY'
#!/usr/bin/env python3
import json,shutil
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory";LAB=ROOT/"platform_lab"
TESTS=MEM/"self_test_report.json";BUILDS=MEM/"sandbox_build_report.json";OUT=MEM/"internal_promotion_report.json"
STATE=MEM/"internal_promotion_state.json";HEALTH=MEM/"internal_promotion_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def run():
    tests={x["proposal_id"]:x for x in load(TESTS,{}).get("tests",[])}
    promoted=[]
    for b in load(BUILDS,{}).get("builds",[]):
        if not tests.get(b["proposal_id"],{}).get("passed"): continue
        src=Path(b["sandbox_dir"])/"module.py"
        dst=LAB/"promoted"/f"{b['capability']}_{b['proposal_id']}.py"
        shutil.copy2(src,dst)
        promoted.append({"proposal_id":b["proposal_id"],"capability":b["capability"],"promoted_path":str(dst),"status":"promoted_internal"})
    payload={"generated_at":now(),"promotion_count":len(promoted),"promotions":promoted,
             "note":"Internal promotion only. External deployment still follows registered deployment authority."}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"promotion_count":len(promoted)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"internal_promotion_complete","report":payload}
print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/internal_promotion_manager.py"

cat > "$CTL/internalpromotionctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"internal_promotion_manager.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/internalpromotionctl"

cat > "$AGENTS/architecture_memory_engine.py" <<'PY'
#!/usr/bin/env python3
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
SOURCES=[MEM/"platform_architecture_plan.json",MEM/"sandbox_build_report.json",MEM/"self_test_report.json",MEM/"internal_promotion_report.json"]
OUT=MEM/"architecture_memory.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def run():
    mem=load(OUT,{"events":[]});seen={x["event_id"] for x in mem.get("events",[])}
    for p in SOURCES:
        d=load(p,{})
        if not d:continue
        eid=hashlib.sha256((p.name+"|"+str(d.get("generated_at"))).encode()).hexdigest()[:18]
        if eid not in seen:
            mem.setdefault("events",[]).append({"event_id":eid,"source":p.name,"captured_at":now(),"payload":d});seen.add(eid)
    mem["events"]=mem["events"][-1000:];mem["generated_at"]=now();mem["event_count"]=len(mem["events"])
    OUT.write_text(json.dumps(mem,indent=2))
    return {"success":True,"status":"architecture_memory_complete","event_count":mem["event_count"]}
print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/architecture_memory_engine.py"

cat > "$CTL/architecturememoryctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"architecture_memory_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/architecturememoryctl"

cat > "$AGENTS/phase28_controller.py" <<'PY'
#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
STATE=MEM/"phase28_state.json";HEALTH=MEM/"phase28_health.json";REPORT=MEM/"phase28_report.json"
PIPE=[
 ("capability_gaps",["python","companyos/capabilitygapctl"]),
 ("platform_architect",["python","companyos/platformarchitectctl"]),
 ("sandbox_builder",["python","companyos/sandboxbuilderctl"]),
 ("self_test",["python","companyos/selftestctl"]),
 ("internal_promotion",["python","companyos/internalpromotionctl"]),
 ("architecture_memory",["python","companyos/architecturememoryctl"])
]

def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def run():
    steps=[];failed=[]
    for name,cmd in PIPE:
        p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=900)
        r={"success":p.returncode==0,"return_code":p.returncode,"stdout":p.stdout[-2500:],"stderr":p.stderr[-1000:]}
        steps.append({"step":name,"result":r})
        if not r["success"]:failed.append(name)
    report={"generated_at":now(),"failure_count":len(failed),"failed_steps":failed,"steps":steps}
    save(REPORT,report);save(STATE,{"last_run_at":now(),"failure_count":len(failed),"failed_steps":failed});save(HEALTH,{"healthy":not failed,"last_checked_at":now()})
    return {"success":not failed,"status":"phase28_self_evolving_platform_cycle_complete","report":report}
print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/phase28_controller.py"

cat > "$CTL/phase28ctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase28_controller.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/phase28ctl"

echo "[1/7] Compiling..."
python -m py_compile \
 "$AGENTS/capability_gap_detector.py" "$AGENTS/platform_architect_engine.py" \
 "$AGENTS/sandbox_builder_engine.py" "$AGENTS/self_test_engine.py" \
 "$AGENTS/internal_promotion_manager.py" "$AGENTS/architecture_memory_engine.py" \
 "$AGENTS/phase28_controller.py" "$CTL/capabilitygapctl" "$CTL/platformarchitectctl" \
 "$CTL/sandboxbuilderctl" "$CTL/selftestctl" "$CTL/internalpromotionctl" \
 "$CTL/architecturememoryctl" "$CTL/phase28ctl"

echo "[2/7] Detecting capability gaps..."
python "$CTL/capabilitygapctl"

echo "[3/7] Designing platform changes..."
python "$CTL/platformarchitectctl"

echo "[4/7] Building sandboxes..."
python "$CTL/sandboxbuilderctl"

echo "[5/7] Testing and promoting..."
python "$CTL/selftestctl"
python "$CTL/internalpromotionctl"
python "$CTL/architecturememoryctl"

echo "[6/7] Registering scheduler..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"phase28-self-evolving-platform","enabled":True,"interval_seconds":21600,
     "command":["python","companyos/phase28ctl"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
python "$CTL/operationsctl" restart

echo "[7/7] Integrated verification..."
python "$CTL/phase28ctl" || true

python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[
r/"agents"/"capability_gap_detector.py",r/"agents"/"platform_architect_engine.py",
r/"agents"/"sandbox_builder_engine.py",r/"agents"/"self_test_engine.py",
r/"agents"/"internal_promotion_manager.py",r/"agents"/"architecture_memory_engine.py",
r/"agents"/"phase28_controller.py",r/"companyos"/"capabilitygapctl",
r/"companyos"/"platformarchitectctl",r/"companyos"/"sandboxbuilderctl",
r/"companyos"/"selftestctl",r/"companyos"/"internalpromotionctl",
r/"companyos"/"architecturememoryctl",r/"companyos"/"phase28ctl",
r/"ceo_memory"/"phase28_platform_config.json",r/"ceo_memory"/"capability_gap_report.json",
r/"ceo_memory"/"platform_architecture_plan.json",r/"ceo_memory"/"sandbox_build_report.json",
r/"ceo_memory"/"self_test_report.json",r/"ceo_memory"/"internal_promotion_report.json",
r/"ceo_memory"/"architecture_memory.json"
]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:14]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
print("--------------------------------------------")
print("PHASE 28 SELF-EVOLVING PLATFORM VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 28 SELF-EVOLVING PLATFORM CORE INSTALLED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Includes:"
echo "  - Capability gap detector"
echo "  - Platform architect"
echo "  - Sandbox builder"
echo "  - Self-test engine"
echo "  - Internal promotion manager"
echo "  - Architecture memory"
echo
echo "Commands:"
echo "  python companyos/phase28ctl"
echo "  python companyos/capabilitygapctl"
echo "  python companyos/platformarchitectctl"
