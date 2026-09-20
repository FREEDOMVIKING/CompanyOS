#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"

echo "===== COMPANYOS V27.9.5 CONTROLLED ACTIVATION + THROUGHPUT ====="

SUP="$(pgrep -f 'companyos.runtime.service_supervisor' | head -1 || true)"
OLD="$(pgrep -f 'companyos.runtime.continuous_goal_runtime' | tail -1 || true)"

echo "SUPERVISOR_PID=${SUP:-none}"
echo "CONTINUOUS_OLD_PID=${OLD:-none}"

if [ -z "${SUP:-}" ]; then
  echo "ABORT: supervisor is not running"
  exit 2
fi

python - <<'PY'
from pathlib import Path
s=Path("companyos/runtime/autonomous_task_dispatcher.py").read_text()
assert "V27_9_4A_LIVE_HANDLER_TIMEOUT" in s
assert "run_bounded(lambda: handler(task))" in s
print("V27_9_4A_SOURCE=PASS")
PY

snapshot() {
python - <<'PY'
import json
from pathlib import Path
from collections import Counter
root=Path.home()/".companyos_runtime"/"task_queue"
c=Counter()
for p in root.glob("*.json"):
    try:
        x=json.loads(p.read_text())
        c[str(x.get("state","UNKNOWN")).upper()] += 1
    except Exception:
        c["UNREADABLE"] += 1
print(dict(c))
PY
}

echo "===== QUEUE BEFORE ====="
snapshot

echo "===== RELOAD CONTINUOUS CHILD ONLY ====="
if [ -n "${OLD:-}" ]; then
  kill "$OLD" 2>/dev/null || true
fi

NEW=""
for i in $(seq 1 30); do
  sleep 1
  CAND="$(pgrep -f 'companyos.runtime.continuous_goal_runtime' | tail -1 || true)"
  if [ -n "${CAND:-}" ] && [ "${CAND:-}" != "${OLD:-}" ]; then
    NEW="$CAND"
    break
  fi
  echo "waiting_for_child_restart=${i}s"
done

if [ -z "${NEW:-}" ]; then
  echo "ABORT: continuous runtime did not respawn"
  pgrep -af 'companyos.runtime.service_supervisor' || true
  exit 3
fi

echo "CONTINUOUS_NEW_PID=$NEW"
echo "CHILD_RELOAD=PASS"

echo "===== 120 SECOND LIVE OBSERVATION ====="
python - <<'PY'
import json,time
from pathlib import Path
from collections import Counter
root=Path.home()/".companyos_runtime"/"task_queue"

def snap():
    c=Counter()
    for p in root.glob("*.json"):
        try:
            x=json.loads(p.read_text())
            c[str(x.get("state","UNKNOWN")).upper()] += 1
        except Exception:
            c["UNREADABLE"] += 1
    return c

start=snap()
print("T+000",dict(start),flush=True)
for elapsed in range(15,121,15):
    time.sleep(15)
    cur=snap()
    print(f"T+{elapsed:03d}",dict(cur),
          "completed_delta=",cur.get("COMPLETED",0)-start.get("COMPLETED",0),
          "queued_delta=",cur.get("QUEUED",0)-start.get("QUEUED",0),
          "failed_delta=",cur.get("FAILED",0)-start.get("FAILED",0),
          flush=True)
end=snap()
print("FINAL_COMPLETED_DELTA=",end.get("COMPLETED",0)-start.get("COMPLETED",0))
print("FINAL_QUEUED_DELTA=",end.get("QUEUED",0)-start.get("QUEUED",0))
print("FINAL_FAILED_DELTA=",end.get("FAILED",0)-start.get("FAILED",0))
PY

echo "===== RUNTIME STATE ====="
python - <<'PY'
import json
from pathlib import Path
for name in ("continuous_goal_runtime_state.json","autonomous_ceo_runtime_service.json"):
    p=Path.home()/".companyos_runtime"/name
    print("---",name,"---")
    if not p.exists():
        print("MISSING")
        continue
    try:
        d=json.loads(p.read_text())
        keep={k:v for k,v in d.items() if k in (
            "running","ready","cycles","cycle_count","goals_processed",
            "idle_cycles","consecutive_failures","last_reason","reason",
            "cycles_dispatched_this_tick","last_cycle_unix","updated_at_unix"
        )}
        print(json.dumps(keep,indent=2,default=str))
    except Exception as e:
        print("READ_ERROR",type(e).__name__,str(e))
PY

echo "===== RECENT TIMEOUT/FAILURES ====="
python - <<'PY'
import json
from pathlib import Path
rows=[]
root=Path.home()/".companyos_runtime"/"task_queue"
for p in root.glob("*.json"):
    try:
        x=json.loads(p.read_text())
    except Exception:
        continue
    text=json.dumps(x,default=str).lower()
    if "timeout" in text or str(x.get("state","")).upper()=="FAILED":
        rows.append((p.stat().st_mtime,p.name,x))
for _,name,x in sorted(rows,reverse=True)[:8]:
    print(name,x.get("state"),x.get("task_type"),
          str(x.get("last_error") or x.get("error") or "")[:260])
PY

echo "===== PROCESS CHECK ====="
pgrep -af 'companyos.runtime.service_supervisor' || true
pgrep -af 'companyos.runtime.continuous_goal_runtime' || true

echo "===== V27.9.5 COMPLETE ====="
echo "SUPERVISOR_RESTARTED=NO"
echo "CONTINUOUS_CHILD_RELOADED=YES"
echo "QUEUE_RECORDS_DELETED=0"
echo "FINANCE_CONNECTORS_CHANGED=NO"
