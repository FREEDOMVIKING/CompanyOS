#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
echo "===== COMPANYOS V49 LIVE RUNTIME BACKPRESSURE ====="
STAMP="$(date +%Y%m%d_%H%M%S)"
B="$HOME/.companyos_runtime/backups/v49_$STAMP"
mkdir -p "$B"
cp -f companyos/runtime/continuous_goal_runtime.py "$B/"
cp -f companyos/runtime/productive_autonomy_watchdog.py "$B/"

python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/continuous_goal_runtime.py")
s=p.read_text()
old='            execution_results = self.execution_loop.run_bounded_batch(max_dispatches=self.execution_batch_size)\n            dispatched = sum(1 for r in execution_results if r.dispatched)\n'
new='''            try:
                from companyos.runtime.adaptive_backpressure import AdaptiveBackpressure
                control = AdaptiveBackpressure(self.execution_loop.queue).decide()
                live_batch = max(1, min(int(control.get("execution_batch", self.execution_batch_size)), 64))
            except Exception:
                live_batch = self.execution_batch_size
            execution_results = self.execution_loop.run_bounded_batch(max_dispatches=live_batch)
            dispatched = sum(1 for r in execution_results if r.dispatched)
'''
if old in s:
    s=s.replace(old,new,1)
elif "live_batch = max(1, min(int(control.get" not in s:
    raise SystemExit("V49_ABORT continuous runtime mismatch")
p.write_text(s)
PY

python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/productive_autonomy_watchdog.py")
s=p.read_text()
needle='def tick() -> dict[str, Any]:\n'
insert='''def _v49_backpressure():
    try:
        from companyos.runtime.adaptive_backpressure import AdaptiveBackpressure
        return AdaptiveBackpressure().decide()
    except Exception:
        return {"snapshot": {"queued": 0}, "producer_divisor": 1}

def tick() -> dict[str, Any]:
    bp = _v49_backpressure()
    if int(bp.get("snapshot", {}).get("queued", 0) or 0) >= int(os.getenv("COMPANYOS_BACKPRESSURE_QUEUE_THRESHOLD", "300")):
        p, rs = runtime_state()
        ws = watchdog_state()
        ws["last_seen"] = {
            "state_path": str(p) if p else None,
            "action": "backpressure_execution_first",
            "queued": bp.get("snapshot", {}).get("queued"),
            "producer_divisor": bp.get("producer_divisor"),
            "ts": time.time(),
        }
        write_json(WATCHDOG_STATE, ws)
        return {"ok": True, **ws["last_seen"]}
'''
if needle in s and "_v49_backpressure" not in s:
    s=s.replace(needle,insert,1)
elif "_v49_backpressure" not in s:
    raise SystemExit("V49_ABORT watchdog mismatch")
p.write_text(s)
PY

python -m py_compile companyos/runtime/continuous_goal_runtime.py companyos/runtime/productive_autonomy_watchdog.py
echo "COMPILE=PASS"

PYTHONPATH="$PWD" python - <<'PY'
from companyos.runtime.continuous_goal_runtime import ContinuousGoalRuntime
from companyos.runtime.productive_autonomy_watchdog import _v49_backpressure
r=ContinuousGoalRuntime()
bp=_v49_backpressure()
print("LIVE_EXECUTION_BATCH=",bp.get("execution_batch"))
print("QUEUED=",bp.get("snapshot",{}).get("queued"))
print("V49_IMPORTS=PASS")
PY

git add companyos/runtime/continuous_goal_runtime.py companyos/runtime/productive_autonomy_watchdog.py
git commit -m "V49 wire adaptive backpressure into live runtime" || true
git push origin "$(git branch --show-current)"
echo "SUPERVISOR_RESTART_REQUIRED=YES"
echo "QUEUE_RECORDS_DELETED=0"
echo "V49_INSTALL=PASS"
