#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase18_step20_$(date +%Y%m%d_%H%M%S)"
cd "$ROOT"; mkdir -p "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " Phase 18 Step 20 - Full Autonomous Integration & Validation"
echo "============================================================"

for f in "$CTL/phase18ctl" "$MEM/phase18_integration_report.json" \
 "$MEM/phase18_integration_health.json"; do
 [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$CTL/phase18ctl" <<'PY'
#!/usr/bin/env python3
import json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

R=Path.home()/"companyos"; M=R/"ceo_memory"; C=R/"companyos"
REPORT=M/"phase18_integration_report.json"; HEALTH=M/"phase18_integration_health.json"

CHECKS=[
 ("operations",["operationsctl","status"]),
 ("recovery",["recoveryctl","status"]),
 ("learning",["learningctl","status"]),
 ("resources",["resourcctl","status"]),
 ("actions",["actionctl","status"]),
 ("health",["healthctl","status"]),
 ("mission",["missionctl","status"]),
 ("governance",["governancectl","status"]),
 ("outcomes",["outcomectl","status"]),
 ("strategy_feedback",["strategyfeedbackctl","status"]),
 ("readiness",["readinessctl","status"])
]

def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
 t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def run(name,args):
 p=C/args[0]
 if not p.exists(): return {"name":name,"success":False,"error":"controller_missing"}
 try:
  x=subprocess.run([sys.executable,str(p),*args[1:]],cwd=R,text=True,capture_output=True,timeout=120)
  return {"name":name,"success":x.returncode==0,"return_code":x.returncode,
          "stdout":x.stdout[-2000:],"stderr":x.stderr[-1000:]}
 except Exception as e:return {"name":name,"success":False,"error":str(e)}

def validate():
 results=[run(n,a) for n,a in CHECKS]
 failed=[x for x in results if not x["success"]]
 scheduler=run("scheduler",["operationsctl","status"])
 if not scheduler["success"]: failed.append(scheduler)
 report={"generated_at":now(),"checks":len(results)+1,"failures":len(failed),
         "results":results,"scheduler":scheduler,
         "phase18_complete":len(failed)==0}
 save(REPORT,report)
 save(HEALTH,{"healthy":len(failed)==0,"last_validated_at":now(),
              "checks":len(results)+1,"failures":len(failed),
              "phase18_complete":len(failed)==0})
 return {"success":len(failed)==0,
         "status":"phase18_validation_complete" if not failed else "phase18_validation_failed",
         "report":report}

def status():
 try:r=json.loads(REPORT.read_text())
 except:r={}
 try:h=json.loads(HEALTH.read_text())
 except:h={}
 return {"success":True,"status":"phase18_status","health":h,"report":r}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=validate() if a=="validate" else status() if a=="status" else {
 "success":False,"status":"unknown_action","allowed":["validate","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY

chmod +x "$CTL/phase18ctl"

echo "[1/5] Compiling final integration controller..."
python -m py_compile "$CTL/phase18ctl"

echo "[2/5] Running complete Phase 18 validation..."
python "$CTL/phase18ctl" validate

echo "[3/5] Running readiness check..."
python "$CTL/readinessctl" check

echo "[4/5] Refreshing mission control..."
python "$CTL/missionctl" build

echo "[5/5] Final verification..."
python - <<'PY'
import json
from pathlib import Path
r=Path.home()/"companyos";m=r/"ceo_memory";errors=[]
required=[
"operationsctl","recoveryctl","learningctl","resourcctl","actionctl",
"healthctl","missionctl","governancectl","outcomectl",
"strategyfeedbackctl","readinessctl","phase18ctl"]
for x in required:
 p=r/"companyos"/x
 if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing controller: {x}")

try:
 h=json.loads((m/"phase18_integration_health.json").read_text())
 if h.get("phase18_complete") is not True:
  errors.append("Phase 18 integration validation did not pass")
except Exception as e:errors.append(f"Integration health error: {e}")

try:
 sched=json.loads((m/"autonomous_operations_config.json").read_text())
 enabled={x.get("id") for x in sched.get("jobs",[]) if x.get("enabled") is True}
 expected={"learning-feedback","exception-recovery","resource-workload-optimizer",
 "internal-action-engine","autonomous-health-supervisor","mission-control",
 "governance-router","outcome-tracker","strategy-feedback-loop","dependency-readiness"}
 missing=sorted(expected-enabled)
 if missing:errors.append("Missing enabled scheduler jobs: "+", ".join(missing))
except Exception as e:errors.append(f"Scheduler verification error: {e}")

print("--------------------------------------------")
print("Phase 18 Step 20 FINAL verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 18 COMPLETE"
echo " FULL AUTONOMOUS OPERATING LOOP INTEGRATED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Final status:"
echo "  python companyos/phase18ctl status"
echo "Revalidate:"
echo "  python companyos/phase18ctl validate"
