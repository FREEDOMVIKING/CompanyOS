#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
echo "===== COMPANYOS V27.9.2 LIVE DISPATCHER WIRING ====="
TS="$(date +%Y%m%d_%H%M%S)"
B="$HOME/.companyos_runtime/backups/v27_9_2_$TS"; mkdir -p "$B"
for f in companyos/runtime/execution_drain_engine.py companyos/runtime/continuous_goal_runtime.py; do
  [ -f "$f" ] && cp -a "$f" "$B/$(basename "$f")"
done
echo "BACKUP=$B"

python - <<'PY'
from companyos.runtime.continuous_goal_runtime import ContinuousGoalRuntime
r=ContinuousGoalRuntime(); loop=r.ceo_runtime.ceo.execution_loop
assert hasattr(loop,"dispatcher") and hasattr(loop.dispatcher,"dispatch_next")
base=getattr(loop.dispatcher,"dispatcher",None)
assert base is not None and hasattr(base,"handlers")
print("LIVE_CHAIN=continuous_goal_runtime.ceo_runtime.ceo.execution_loop.dispatcher")
print("LIVE_HANDLERS=",sorted(base.handlers)); print("CHAIN_CONTRACT=PASS")
PY

cat > companyos/runtime/execution_drain_engine.py <<'PY'
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue

@dataclass(frozen=True)
class DrainResult:
    attempted: int
    dispatched: int
    stopped_reason: str
    last_result: Any = None

class ExecutionDrainEngine:
    def __init__(self, queue: AutonomousTaskQueue, dispatcher: Any, batch_size: int = 32):
        if dispatcher is None or not hasattr(dispatcher, "dispatch_next"):
            raise TypeError("live_dependency_dispatcher_required")
        self.queue=queue
        self.dispatcher=dispatcher
        self.batch_size=max(1,min(int(batch_size),64))

    def drain_once(self) -> DrainResult:
        attempted=dispatched=0
        last=None
        for _ in range(self.batch_size):
            attempted += 1
            last=self.dispatcher.dispatch_next()
            if not getattr(last,"dispatched",False):
                return DrainResult(attempted,dispatched,str(getattr(last,"reason","not_dispatched")),last)
            dispatched += 1
        return DrainResult(attempted,dispatched,"batch_limit",last)
PY

python -m py_compile companyos/runtime/execution_drain_engine.py

python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/continuous_goal_runtime.py")
s=p.read_text()
if "def drain_execution_backlog(" not in s:
    marker="    def request_stop(self):\n"
    lines=[
      "    def drain_execution_backlog(self, batch_size: int = 32):",
      "        from companyos.runtime.execution_drain_engine import ExecutionDrainEngine",
      "        loop = self.ceo_runtime.ceo.execution_loop",
      "        return ExecutionDrainEngine(",
      "            queue=loop.queue, dispatcher=loop.dispatcher, batch_size=batch_size",
      "        ).drain_once()",
      "",
      ""
    ]
    block="\n".join(lines)
    if marker not in s: raise SystemExit("PATCH_ABORT=request_stop_marker_not_found")
    p.write_text(s.replace(marker,block+marker,1))
print("RUNTIME_WIRING_PATCH=PASS")
PY

python -m py_compile companyos/runtime/continuous_goal_runtime.py companyos/runtime/execution_drain_engine.py
echo "COMPILE=PASS"

python - <<'PY'
from companyos.runtime.continuous_goal_runtime import ContinuousGoalRuntime
from companyos.runtime.execution_drain_engine import ExecutionDrainEngine
r=ContinuousGoalRuntime(); loop=r.ceo_runtime.ceo.execution_loop
base=getattr(loop.dispatcher,"dispatcher",None)
assert base is not None
assert {"research","planning","build"}.issubset(set(base.handlers))
e=ExecutionDrainEngine(loop.queue,loop.dispatcher,batch_size=1)
assert e.dispatcher is loop.dispatcher and e.queue is loop.queue
print("REGISTERED_HANDLERS=",sorted(base.handlers))
print("EXACT_LIVE_DISPATCHER_INJECTION=PASS")
PY

echo "===== SUPERVISOR PRESERVED ====="
pgrep -af 'companyos.runtime.service_supervisor' || true

python - <<'PY'
from collections import Counter
from pathlib import Path
import json
from companyos.runtime.continuous_goal_runtime import ContinuousGoalRuntime
root=Path.home()/".companyos_runtime"/"task_queue"
def counts():
    c=Counter()
    for f in root.glob("*.json"):
        try: c[str(json.loads(f.read_text()).get("state","UNKNOWN")).upper()] += 1
        except Exception: c["UNREADABLE"] += 1
    return dict(c)
before=counts(); r=ContinuousGoalRuntime()
res=r.drain_execution_backlog(batch_size=8); after=counts()
print("BEFORE=",before); print("DRAIN_ATTEMPTED=",res.attempted)
print("DRAIN_DISPATCHED=",res.dispatched); print("DRAIN_STOP_REASON=",res.stopped_reason)
print("AFTER=",after); print("V27.9.2=PASS")
PY

git add companyos/runtime/execution_drain_engine.py companyos/runtime/continuous_goal_runtime.py
if ! git diff --cached --quiet; then
  git commit -m "V27.9.2 wire drain engine to live CEO dispatcher"
  git push origin "$(git branch --show-current)" || echo "PUSH_WARNING=commit_saved_locally"
else
  echo "GIT=no_new_diff"
fi
echo "===== V27.9.2 COMPLETE ====="
echo "SUPERVISOR_RESTARTED=NO"
echo "QUEUE_RECORDS_DELETED=0"
echo "DEPENDENCY_GATES_BYPASSED=NO"
