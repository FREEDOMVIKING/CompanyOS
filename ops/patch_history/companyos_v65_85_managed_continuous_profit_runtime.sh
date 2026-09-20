#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

RUNTIME="$HOME/.companyos_runtime"
BIN="$RUNTIME/bin"
LOGDIR="$RUNTIME/logs"
PIDFILE="$RUNTIME/continuous_profit_runtime.pid"
LOGFILE="$LOGDIR/continuous_profit_runtime.log"
STATEFILE="$RUNTIME/continuous_goal_runtime_state.json"
STOPFILE="$RUNTIME/continuous_goal_runtime.stop"
RUNNER="$BIN/v65_85_continuous_profit_runtime.py"

mkdir -p "$BIN" "$LOGDIR"

write_runner() {
cat > "$RUNNER" <<'PY'
from __future__ import annotations
import json
import os
import time
from pathlib import Path

from companyos.runtime.continuous_goal_runtime import ContinuousGoalRuntime

interval = max(2, int(os.getenv("COMPANYOS_CONTINUOUS_INTERVAL_SECONDS", "5")))
max_failures = max(1, int(os.getenv("COMPANYOS_CONTINUOUS_MAX_FAILURES", "5")))

print("COMPANYOS_V65_85_CONTINUOUS_PROFIT_RUNTIME=STARTING", flush=True)
print("INTERVAL_SECONDS=", interval, flush=True)
print("MAX_FAILURES=", max_failures, flush=True)
print("PROFIT_AUTOSEED_ENABLED=", os.getenv("COMPANYOS_PROFIT_AUTOSEED_ENABLED", "1"), flush=True)
print("PROFIT_AUTOSEED_COOLDOWN_SECONDS=", os.getenv("COMPANYOS_PROFIT_AUTOSEED_COOLDOWN_SECONDS", "300"), flush=True)
print("EXTERNAL_ACTIONS_THIS_RUNTIME=INTERNAL_ORCHESTRATION_ONLY", flush=True)

runtime = ContinuousGoalRuntime(
    interval_seconds=interval,
    max_failures=max_failures,
)

state = runtime.run()

print("COMPANYOS_V65_85_CONTINUOUS_PROFIT_RUNTIME=STOPPED", flush=True)
print("FINAL_STATE=", json.dumps({
    "running": state.running,
    "ready": state.ready,
    "cycles": state.cycles,
    "goals_processed": state.goals_processed,
    "idle_cycles": state.idle_cycles,
    "execution_dispatched": state.execution_dispatched,
    "execution_failures": state.execution_failures,
    "scheduler_failures": state.scheduler_failures,
    "ceo_failures": state.ceo_failures,
    "auto_seeded_profit_goals": getattr(state, "auto_seeded_profit_goals", 0),
    "last_reason": state.last_reason,
    "last_orchestration_id": state.last_orchestration_id,
}, sort_keys=True), flush=True)
PY
chmod 700 "$RUNNER"
}

verify_source() {
python - <<'PY'
from pathlib import Path
import py_compile

p = Path.home() / "companyos/companyos/runtime/continuous_goal_runtime.py"
if not p.exists():
    raise SystemExit("V65_85_ABORT=continuous_goal_runtime_missing")

src = p.read_text(errors="ignore")
required = [
    "V65.83 idle profit auto-seed",
    "_auto_seed_profit_goal_if_idle",
    "COMPANYOS_PROFIT_AUTOSEED_ENABLED",
    "COMPANYOS_PROFIT_AUTOSEED_COOLDOWN_SECONDS",
    "profit_goal_auto_seeded_and_orchestrated",
]
missing = [x for x in required if x not in src]
print("V65_83_REQUIRED_MARKERS_MISSING=", missing)
if missing:
    raise SystemExit("V65_85_ABORT=v65_83_patch_not_present")

py_compile.compile(str(p), doraise=True)
print("CONTINUOUS_RUNTIME_COMPILE=PASS")
PY
}

preflight_state() {
python - <<'PY'
from pathlib import Path
from collections import Counter
import json
import sqlite3

rt = Path.home() / ".companyos_runtime"
qdir = rt / "task_queue"
db = rt / "execution_kernel.sqlite3"
odir = rt / "ceo_orchestrations"
idir = rt / "goal_intake"

def read_jsons(d):
    vals = []
    bad = []
    if not d.exists():
        return vals, bad
    for p in d.glob("*.json"):
        try:
            vals.append(json.loads(p.read_text(errors="ignore")))
        except Exception as exc:
            bad.append((str(p), type(exc).__name__))
    return vals, bad

tasks, badq = read_jsons(qdir)
orch, bado = read_jsons(odir)
intake, badi = read_jsons(idir)

states = Counter(str(x.get("state") or "UNKNOWN") for x in tasks)
running_orch = sum(1 for x in orch if str(x.get("state")) == "RUNNING")
pending_intake = sum(1 for x in intake if str(x.get("state")) in ("PENDING", "CLAIMED"))

con = sqlite3.connect(str(db))
try:
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    db_count = con.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
finally:
    con.close()

print("PREFLIGHT_QUEUE_STATES=", dict(sorted(states.items())))
print("PREFLIGHT_RUNNING_ORCHESTRATIONS=", running_orch)
print("PREFLIGHT_PENDING_OR_CLAIMED_INTAKES=", pending_intake)
print("PREFLIGHT_DB_INTEGRITY=", integrity)
print("PREFLIGHT_QUEUE_MINUS_DB_DELTA=", len(tasks) - db_count)
print("PREFLIGHT_UNREADABLE_JSON=", len(badq) + len(bado) + len(badi))

if badq or bado or badi:
    raise SystemExit("V65_85_ABORT=unreadable_runtime_json")
if integrity != "ok":
    raise SystemExit("V65_85_ABORT=db_integrity_failed")
if len(tasks) != db_count:
    raise SystemExit("V65_85_ABORT=projection_cardinality_mismatch")
if states.get("CLAIMED", 0) or states.get("RUNNING", 0):
    raise SystemExit("V65_85_ABORT=active_execution_task_present")
PY
}

status_cmd() {
python - <<'PY'
from pathlib import Path
from collections import Counter
import json
import os

rt = Path.home() / ".companyos_runtime"
pidfile = rt / "continuous_profit_runtime.pid"
statefile = rt / "continuous_goal_runtime_state.json"
qdir = rt / "task_queue"
odir = rt / "ceo_orchestrations"
idir = rt / "goal_intake"

pid = None
alive = False
if pidfile.exists():
    try:
        pid = int(pidfile.read_text().strip())
        os.kill(pid, 0)
        alive = True
    except Exception:
        alive = False

def read_jsons(d):
    vals = []
    if d.exists():
        for p in d.glob("*.json"):
            try:
                vals.append(json.loads(p.read_text(errors="ignore")))
            except Exception:
                pass
    return vals

tasks = read_jsons(qdir)
orch = read_jsons(odir)
intakes = read_jsons(idir)
states = Counter(str(x.get("state") or "UNKNOWN") for x in tasks)

print("MANAGED_RUNTIME_PID=", pid)
print("MANAGED_RUNTIME_ALIVE=", alive)
print("QUEUE_STATES=", dict(sorted(states.items())))
print("RUNNING_ORCHESTRATIONS=", sum(1 for x in orch if str(x.get("state")) == "RUNNING"))
print("PENDING_OR_CLAIMED_INTAKES=", sum(1 for x in intakes if str(x.get("state")) in ("PENDING", "CLAIMED")))

auto = [
    x for x in intakes
    if isinstance(x.get("metadata"), dict) and x["metadata"].get("auto_seeded") is True
]
auto.sort(key=lambda x: float(x.get("updated_at_unix") or x.get("created_at_unix") or 0), reverse=True)
if auto:
    latest = auto[0]
    print("LATEST_AUTO_PROFIT_INTAKE=", {
        "intake_id": latest.get("intake_id"),
        "state": latest.get("state"),
        "orchestration_id": latest.get("orchestration_id"),
    })

if statefile.exists():
    try:
        state = json.loads(statefile.read_text())
        print("CONTINUOUS_STATE=", {
            "running": state.get("running"),
            "ready": state.get("ready"),
            "cycles": state.get("cycles"),
            "goals_processed": state.get("goals_processed"),
            "idle_cycles": state.get("idle_cycles"),
            "execution_dispatched": state.get("execution_dispatched"),
            "execution_failures": state.get("execution_failures"),
            "scheduler_failures": state.get("scheduler_failures"),
            "ceo_failures": state.get("ceo_failures"),
            "auto_seeded_profit_goals": state.get("auto_seeded_profit_goals"),
            "last_reason": state.get("last_reason"),
            "last_orchestration_id": state.get("last_orchestration_id"),
            "updated_at_unix": state.get("updated_at_unix"),
        })
    except Exception as exc:
        print("CONTINUOUS_STATE_READ_ERROR=", type(exc).__name__, str(exc))
PY
}

start_cmd() {
    verify_source
    preflight_state
    write_runner

    if [ -f "$PIDFILE" ]; then
        oldpid="$(cat "$PIDFILE" 2>/dev/null || true)"
        if [ -n "${oldpid:-}" ] && kill -0 "$oldpid" 2>/dev/null; then
            echo "V65_85_ALREADY_RUNNING_PID=$oldpid"
            status_cmd
            exit 0
        fi
        rm -f "$PIDFILE"
    fi

    rm -f "$STOPFILE"

    # Default: one new profit objective at most every 5 minutes when globally idle.
    export COMPANYOS_PROFIT_AUTOSEED_ENABLED="${COMPANYOS_PROFIT_AUTOSEED_ENABLED:-1}"
    export COMPANYOS_PROFIT_AUTOSEED_COOLDOWN_SECONDS="${COMPANYOS_PROFIT_AUTOSEED_COOLDOWN_SECONDS:-300}"
    export COMPANYOS_CONTINUOUS_INTERVAL_SECONDS="${COMPANYOS_CONTINUOUS_INTERVAL_SECONDS:-5}"
    export COMPANYOS_CONTINUOUS_MAX_FAILURES="${COMPANYOS_CONTINUOUS_MAX_FAILURES:-5}"

    echo "===== STARTING MANAGED CONTINUOUS PROFIT RUNTIME ====="
    echo "LOGFILE=$LOGFILE"
    echo "PROFIT_AUTOSEED_COOLDOWN_SECONDS=$COMPANYOS_PROFIT_AUTOSEED_COOLDOWN_SECONDS"

    nohup env \
        PYTHONPATH="$PYTHONPATH" \
        COMPANYOS_PROFIT_AUTOSEED_ENABLED="$COMPANYOS_PROFIT_AUTOSEED_ENABLED" \
        COMPANYOS_PROFIT_AUTOSEED_COOLDOWN_SECONDS="$COMPANYOS_PROFIT_AUTOSEED_COOLDOWN_SECONDS" \
        COMPANYOS_CONTINUOUS_INTERVAL_SECONDS="$COMPANYOS_CONTINUOUS_INTERVAL_SECONDS" \
        COMPANYOS_CONTINUOUS_MAX_FAILURES="$COMPANYOS_CONTINUOUS_MAX_FAILURES" \
        python -u "$RUNNER" >> "$LOGFILE" 2>&1 < /dev/null &

    pid=$!
    echo "$pid" > "$PIDFILE"
    sleep 3

    if ! kill -0 "$pid" 2>/dev/null; then
        echo "V65_85_START=FAIL"
        echo "===== LAST 100 LOG LINES ====="
        tail -n 100 "$LOGFILE" || true
        exit 1
    fi

    echo "V65_85_MANAGED_RUNTIME_PID=$pid"
    echo "V65_85_START=PASS"
    echo "V65_85_PROFIT_AUTOSEED=ENABLED"
    echo "V65_85_EXTERNAL_ACTION_MODE=INTERNAL_ORCHESTRATION_ONLY"
    status_cmd
    echo "V65_85_COMPLETE"
}

stop_cmd() {
    echo "===== REQUESTING GRACEFUL STOP ====="
    mkdir -p "$RUNTIME"
    printf 'stop\n' > "$STOPFILE"

    pid=""
    [ -f "$PIDFILE" ] && pid="$(cat "$PIDFILE" 2>/dev/null || true)"

    if [ -n "${pid:-}" ] && kill -0 "$pid" 2>/dev/null; then
        for _ in $(seq 1 15); do
            if ! kill -0 "$pid" 2>/dev/null; then
                break
            fi
            sleep 1
        done
    fi

    if [ -n "${pid:-}" ] && kill -0 "$pid" 2>/dev/null; then
        echo "GRACEFUL_STOP_PENDING_PID=$pid"
        echo "Use: kill $pid  # only if it does not stop after another cycle"
    else
        rm -f "$PIDFILE"
        echo "V65_85_STOP=PASS"
    fi

    status_cmd
}

logs_cmd() {
    if [ ! -f "$LOGFILE" ]; then
        echo "NO_LOGFILE=$LOGFILE"
        exit 0
    fi
    tail -n 120 "$LOGFILE"
}

cmd="${1:-start}"
case "$cmd" in
    start) start_cmd ;;
    status) status_cmd ;;
    stop) stop_cmd ;;
    logs) logs_cmd ;;
    *)
        echo "Usage: $0 {start|status|stop|logs}"
        exit 2
        ;;
esac
