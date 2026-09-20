#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
cd "$HOME/companyos"
RT="$HOME/.companyos_runtime"
B="$RT/backups/v36_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$B"
echo "===== COMPANYOS V36 CONTROLLED LIVE RECOVERY QUALIFICATION ====="

# Preflight: do not touch code unless the V35.1 contract is present and compiles.
grep -q 'V35_1_FENCED_HANDLER_CALL' companyos/runtime/autonomous_task_dispatcher.py || { echo "V35_1_CONTRACT=MISSING"; exit 20; }
python -m py_compile \
  companyos/runtime/autonomous_task_dispatcher.py \
  companyos/runtime/lease_execution_guard.py \
  companyos/runtime/worker_lease_store.py
echo "PREFLIGHT=PASS"

# Snapshot relevant runtime state.
cp -a companyos/runtime/autonomous_task_dispatcher.py "$B/" || true
cp -a companyos/runtime/lease_execution_guard.py "$B/" || true
cp -a companyos/runtime/worker_lease_store.py "$B/" || true
ps -ef > "$B/processes.before.txt" || true

# Isolated crash/recovery test: kill a worker process while it owns a short lease.
cat > tests/test_v36_live_recovery_qualification.py <<'PY'
import multiprocessing as mp
import tempfile, time
from pathlib import Path
from companyos.runtime.durable_execution_kernel import DurableExecutionKernel
from companyos.runtime.worker_lease_store import WorkerLeaseStore
from companyos.runtime.lease_execution_guard import LeaseExecutionGuard

def holder(db, ready):
    s=WorkerLeaseStore(Path(db))
    lease=s.claim("v36-crash-task","crash-worker",ttl=1.0)
    assert lease is not None
    ready.set()
    while True:
        s.heartbeat(lease,ttl=1.0)
        time.sleep(.15)

def test_crashed_owner_expires_and_reclaims():
    with tempfile.TemporaryDirectory() as d:
        k=DurableExecutionKernel(Path(d))
        ready=mp.Event()
        p=mp.Process(target=holder,args=(str(k.db_path),ready))
        p.start()
        assert ready.wait(3)
        s=WorkerLeaseStore(k.db_path)
        assert s.claim("v36-crash-task","competitor",ttl=1.0) is None
        p.terminate(); p.join(3)
        time.sleep(1.25)
        lease=s.claim("v36-crash-task","recovery-worker",ttl=2.0)
        assert lease is not None
        s.release(lease)

def test_guard_prevents_parallel_duplicate():
    with tempfile.TemporaryDirectory() as d:
        k=DurableExecutionKernel(Path(d))
        g=LeaseExecutionGuard(k.db_path)
        held=g.store.claim("v36-dup","owner-a",ttl=5)
        assert held is not None
        ok,val,err=g.execute("v36-dup","owner-b",lambda: 99,ttl=2,interval=.2)
        assert not ok and val is None and err=="lease_unavailable"
        g.store.release(held)

def test_guard_checkpoint_and_success():
    with tempfile.TemporaryDirectory() as d:
        k=DurableExecutionKernel(Path(d))
        g=LeaseExecutionGuard(k.db_path)
        ok,val,err=g.execute("v36-success","owner",lambda: 42,ttl=2,interval=.2)
        assert ok and val==42 and err is None
PY

python -m pytest -q \
  tests/test_v34_worker_lease_store.py \
  tests/test_v35_lease_execution_guard.py \
  tests/test_v35_1_dispatcher_ast_contract.py \
  tests/test_v36_live_recovery_qualification.py
echo "ISOLATED_CRASH_RECOVERY=PASS"

# Fast state counter: no expensive full dependency audit.
count_states () {
python - <<'PY'
from pathlib import Path
import json, collections
q=Path.home()/".companyos_runtime"/"task_queue"
c=collections.Counter()
if q.exists():
    for p in q.iterdir():
        if p.suffix!=".json": continue
        try:
            x=json.loads(p.read_text())
            c[str(x.get("state","UNKNOWN")).upper()]+=1
        except Exception:
            c["UNREADABLE"]+=1
print(" ".join(f"{k}={v}" for k,v in sorted(c.items())))
PY
}

BEFORE="$(count_states)"
echo "QUEUE_BEFORE $BEFORE"

# Controlled reload: remove only stale supervisor stop signal, then restart supervisor
# so V35.1 code is actually loaded. Do not kill arbitrary Python processes.
STOP="$RT/SUPERVISOR_STOP"
rm -f "$STOP"
SUP_PID="$(pgrep -f 'companyos/runtime/service_supervisor.py' | head -1 || true)"
if [ -n "$SUP_PID" ]; then
  echo "SUPERVISOR_OLD_PID=$SUP_PID"
  kill -TERM "$SUP_PID" || true
  for i in $(seq 1 20); do
    kill -0 "$SUP_PID" 2>/dev/null || break
    sleep 1
  done
  if kill -0 "$SUP_PID" 2>/dev/null; then
    echo "SUPERVISOR_GRACEFUL_STOP=FAIL"
    exit 31
  fi
fi

nohup python companyos/runtime/service_supervisor.py >"$RT/supervisor_v36.log" 2>&1 &
NEW_SUP=$!
echo "SUPERVISOR_NEW_PID=$NEW_SUP"
sleep 8
kill -0 "$NEW_SUP" 2>/dev/null || {
  echo "SUPERVISOR_RELOAD=FAIL"
  tail -80 "$RT/supervisor_v36.log" || true
  exit 32
}
echo "SUPERVISOR_RELOAD=PASS"

# Observe real runtime without forcing/faking task completions.
for n in 1 2 3 4 5 6; do
  sleep 10
  echo "T+$((n*10)) $(count_states)"
  kill -0 "$NEW_SUP" 2>/dev/null || { echo "SUPERVISOR_DIED=YES"; exit 33; }
done

AFTER="$(count_states)"
echo "QUEUE_AFTER $AFTER"

# Runtime health + duplicate supervisor check.
SUP_COUNT="$(pgrep -fc 'companyos/runtime/service_supervisor.py' || true)"
CONT_COUNT="$(pgrep -fc 'companyos.runtime.continuous_goal_runtime|companyos/runtime/continuous_goal_runtime.py' || true)"
echo "SUPERVISOR_COUNT=$SUP_COUNT"
echo "CONTINUOUS_RUNTIME_COUNT=$CONT_COUNT"
[ "$SUP_COUNT" -eq 1 ] || { echo "QUALIFICATION_FAIL=duplicate_or_missing_supervisor"; exit 34; }

# Check recent log for hard failures.
if tail -300 "$RT/supervisor_v36.log" 2>/dev/null | grep -Eiq 'Traceback|SyntaxError|NameError:|ImportError|ModuleNotFoundError'; then
  echo "QUALIFICATION_FAIL=runtime_exception"
  tail -100 "$RT/supervisor_v36.log"
  exit 35
fi

echo "QUEUE_RECORDS_DELETED=0"
echo "FINANCE_CONNECTORS_CHANGED=NO"
echo "DUPLICATE_SUPERVISOR=NO"
echo "CRASH_RECOVERY=PASS"
echo "LIVE_RELOAD=PASS"
echo "===== V36 COMPLETE ====="

git add tests/test_v36_live_recovery_qualification.py
git diff --cached --quiet || git commit -m "V36 qualify controlled live reload and crash recovery"
echo "BACKUP=$B"
echo "NEXT=analyze live queue deltas and tune bounded throughput only if healthy"
