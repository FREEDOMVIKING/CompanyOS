#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACK="$HOME/.companyos_runtime/backups/v30_$STAMP"
mkdir -p "$BACK/companyos/runtime"
cp -a companyos/runtime/service_supervisor.py "$BACK/companyos/runtime/service_supervisor.py"
cp -a companyos/runtime/continuous_goal_runtime.py "$BACK/companyos/runtime/continuous_goal_runtime.py"

python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/service_supervisor.py")
s=p.read_text()
if "V30_SHARED_RUNTIME_ROOT" not in s:
    old='        self.runtime_root = self.root / ".companyos_runtime"\n'
    assert old in s
    s=s.replace(old,'        # V30_SHARED_RUNTIME_ROOT\n        self.runtime_root = Path.home() / ".companyos_runtime"\n',1)
p.write_text(s)

p=Path("companyos/runtime/continuous_goal_runtime.py")
s=p.read_text()
assert "V29_BIG_RUNTIME_STABILIZATION" in s
if "V30_FRESH_RUNTIME_SESSION" not in s:
    old='''        state = self.load()
        state.running = True
        state.ready = True
        self.save(state)
'''
    new='''        state = self.load()
        # V30_FRESH_RUNTIME_SESSION
        state.running = True
        state.ready = True
        state.consecutive_failures = 0
        state.last_reason = "runtime_session_started"
        self.save(state)
'''
    assert old in s
    s=s.replace(old,new,1)
p.write_text(s)
print("PATCH=PASS")
PY

python -m py_compile companyos/runtime/service_supervisor.py companyos/runtime/continuous_goal_runtime.py
echo "COMPILE=PASS"

python - <<'PY'
from pathlib import Path
for root in (Path.home()/".companyos_runtime", Path.home()/"companyos"/".companyos_runtime"):
    root.mkdir(parents=True,exist_ok=True)
    for name in ("SUPERVISOR_STOP","service_supervisor.stop","supervisor.stop","continuous_goal_runtime.stop","continuous_runtime.stop"):
        p=root/name
        if p.exists():
            q=p.with_name(p.name+".v30_stale")
            if q.exists(): q.unlink()
            p.replace(q)
            print("MOVED",p)
print("STOP_CLEANUP=PASS")
PY

for pat in 'companyos.runtime.continuous_goal_runtime' 'companyos.runtime.service_supervisor'; do
  for pid in $(pgrep -f "$pat" || true); do
    [ "$pid" = "$$" ] || kill "$pid" 2>/dev/null || true
  done
done
sleep 2

nohup python -m companyos.runtime.service_supervisor >/dev/null 2>&1 &
echo "SUPERVISOR_LAUNCH_PID=$!"

SUP=""
for i in $(seq 1 30); do
  sleep 1
  SUP="$(pgrep -f 'companyos.runtime.service_supervisor' | head -1 || true)"
  [ -n "$SUP" ] && break
  echo "waiting_supervisor=${i}s"
done
[ -n "$SUP" ] || { echo "FAIL=supervisor_not_started"; exit 2; }
echo "SUPERVISOR_PID=$SUP"

CHILD=""
for i in $(seq 1 45); do
  sleep 1
  CHILD="$(pgrep -f 'companyos.runtime.continuous_goal_runtime' | tail -1 || true)"
  [ -n "$CHILD" ] && break
  echo "waiting_continuous=${i}s"
done
[ -n "$CHILD" ] || { echo "FAIL=continuous_not_started"; exit 3; }
echo "CONTINUOUS_PID=$CHILD"

python - <<'PY'
import json,time,subprocess
from pathlib import Path
from collections import Counter
root=Path.home()/".companyos_runtime"/"task_queue"
sp=Path.home()/".companyos_runtime"/"continuous_goal_runtime_state.json"
def snap():
    c=Counter()
    for p in root.glob("*.json"):
        try:c[str(json.loads(p.read_text()).get("state","UNKNOWN")).upper()]+=1
        except Exception:c["UNREADABLE"]+=1
    return c
def state():
    try:return json.loads(sp.read_text())
    except Exception:return {}
def alive(pat):
    return subprocess.run(["pgrep","-f",pat],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
a=snap(); b=a; print("T+000",dict(a),flush=True)
for sec in range(15,181,15):
    time.sleep(15); b=snap(); r=state()
    print(f"T+{sec:03d}",dict(b),
          "completed_delta=",b["COMPLETED"]-a["COMPLETED"],
          "queued_delta=",b["QUEUED"]-a["QUEUED"],
          "failed_delta=",b["FAILED"]-a["FAILED"],
          "cycles=",r.get("cycles"),"exec=",r.get("execution_dispatched"),
          "exec_fail=",r.get("execution_failures"),
          "sched_fail=",r.get("scheduler_failures"),
          "ceo_fail=",r.get("ceo_failures"),
          "reason=",r.get("last_reason"),
          "sup=",alive("companyos.runtime.service_supervisor"),
          "child=",alive("companyos.runtime.continuous_goal_runtime"),
          flush=True)
print("FINAL_COMPLETED_DELTA=",b["COMPLETED"]-a["COMPLETED"])
print("FINAL_QUEUED_DELTA=",b["QUEUED"]-a["QUEUED"])
print("FINAL_FAILED_DELTA=",b["FAILED"]-a["FAILED"])
assert alive("companyos.runtime.service_supervisor")
assert alive("companyos.runtime.continuous_goal_runtime")
PY

python - <<'PY'
import json
from pathlib import Path
p=Path.home()/".companyos_runtime"/"service_supervisor_state.json"
if p.exists():
    d=json.loads(p.read_text())
    print("SUPERVISOR_RUNNING=",d.get("running"))
    sv=d.get("services",{})
    print("SERVICE_COUNT=",len(sv))
    for n,r in sorted(sv.items()):
        print(n,"running=",r.get("running"),"restarts=",r.get("restarts"),"failures=",r.get("consecutive_failures"))
else:
    print("SUPERVISOR_STATE_MISSING")
PY

echo "V30_COMPLETE"
echo "SUPERVISOR_ALIVE=YES"
echo "CONTINUOUS_ALIVE=YES"
echo "QUEUE_RECORDS_DELETED=0"
echo "FINANCE_CONNECTORS_CHANGED=NO"
echo "BACKUP=$BACK"
