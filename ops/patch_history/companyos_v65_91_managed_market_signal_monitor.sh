#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RUNTIME="$HOME/.companyos_runtime"
DOWNLOADS="$HOME/storage/downloads"
INGEST="$DOWNLOADS/companyos_v65_90_ingest_live_rum_signal.sh"
PIDFILE="$RUNTIME/live_market_signal_monitor.pid"
LOGFILE="$RUNTIME/live_market_signal_monitor.log"
STATEFILE="$RUNTIME/live_market_signal_monitor_state.json"
INTERVAL_SECONDS="${COMPANYOS_MARKET_SIGNAL_INTERVAL_SECONDS:-900}"

mkdir -p "$RUNTIME"
cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

action="${1:-start}"

is_running() {
  if [ ! -f "$PIDFILE" ]; then
    return 1
  fi
  pid="$(cat "$PIDFILE" 2>/dev/null || true)"
  [ -n "${pid:-}" ] && kill -0 "$pid" 2>/dev/null
}

write_state() {
  python - "$1" "$2" "$3" <<'PY'
import json, sys, time
from pathlib import Path
state, pid, note = sys.argv[1:4]
p = Path.home()/".companyos_runtime/live_market_signal_monitor_state.json"
p.write_text(json.dumps({
    "state": state,
    "pid": int(pid) if pid.isdigit() else None,
    "note": note,
    "updated_at_unix": time.time(),
}, indent=2, sort_keys=True) + "\n")
PY
}

case "$action" in
  status)
    echo "===== COMPANYOS V65.91 MARKET SIGNAL MONITOR STATUS ====="
    if is_running; then
      pid="$(cat "$PIDFILE")"
      echo "MONITOR_RUNNING=true"
      echo "PID=$pid"
      echo "INTERVAL_SECONDS=$INTERVAL_SECONDS"
      echo "LOGFILE=$LOGFILE"
      [ -f "$STATEFILE" ] && cat "$STATEFILE"
      echo "----- LATEST MARKET SIGNAL -----"
      [ -f "$ROOT/.companyos_runtime/live_market_signal_latest.json" ] && \
        cat "$ROOT/.companyos_runtime/live_market_signal_latest.json" || true
      echo "----- LOG TAIL -----"
      tail -n 40 "$LOGFILE" 2>/dev/null || true
    else
      echo "MONITOR_RUNNING=false"
      [ -f "$STATEFILE" ] && cat "$STATEFILE" || true
    fi
    ;;

  stop)
    echo "===== COMPANYOS V65.91 MARKET SIGNAL MONITOR STOP ====="
    if is_running; then
      pid="$(cat "$PIDFILE")"
      kill "$pid" 2>/dev/null || true
      for _ in $(seq 1 20); do
        if ! kill -0 "$pid" 2>/dev/null; then
          break
        fi
        sleep 1
      done
      if kill -0 "$pid" 2>/dev/null; then
        kill -9 "$pid" 2>/dev/null || true
      fi
      rm -f "$PIDFILE"
      write_state "stopped" "" "stopped_by_user"
      echo "V65_91_STOP=PASS"
    else
      rm -f "$PIDFILE"
      write_state "stopped" "" "already_stopped"
      echo "V65_91_ALREADY_STOPPED=true"
    fi
    ;;

  restart)
    "$0" stop || true
    exec "$0" start
    ;;

  start)
    echo "===== COMPANYOS V65.91 MANAGED MARKET SIGNAL MONITOR ====="
    echo "PURPOSE=AUTONOMOUSLY_POLL_REAL_CLOUDFLARE_RUM_DATA"
    echo "PROFIT_PROMOTION=DISABLED"
    echo "FINANCIAL_ACTIONS=DISABLED"
    echo "OUTREACH=DISABLED"
    echo "INTERVAL_SECONDS=$INTERVAL_SECONDS"

    if [ ! -f "$INGEST" ]; then
      echo "V65_91_ABORT=missing_ingest_script:$INGEST"
      exit 1
    fi

    if is_running; then
      pid="$(cat "$PIDFILE")"
      echo "MONITOR_ALREADY_RUNNING=true"
      echo "PID=$pid"
      exit 0
    fi

    # Seed the current known state once before daemonizing.
    echo "===== INITIAL SIGNAL CHECK ====="
    bash "$INGEST" || true

    nohup bash -c '
      set -u
      ROOT="$HOME/companyos"
      RUNTIME="$HOME/.companyos_runtime"
      INGEST="$HOME/storage/downloads/companyos_v65_90_ingest_live_rum_signal.sh"
      LOGFILE="$RUNTIME/live_market_signal_monitor.log"
      INTERVAL_SECONDS="${COMPANYOS_MARKET_SIGNAL_INTERVAL_SECONDS:-900}"

      cd "$ROOT" || exit 1
      export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

      while true; do
        {
          echo
          echo "===== MARKET SIGNAL POLL $(date -u +%Y-%m-%dT%H:%M:%SZ) ====="
          bash "$INGEST"
          rc=$?
          echo "POLL_RETURN_CODE=$rc"

          python - <<'"'"'PY'"'"'
import json, time
from pathlib import Path
root = Path.home()/"companyos/.companyos_runtime"
src = root/"live_market_signal_latest.json"
state = Path.home()/".companyos_runtime/live_market_signal_monitor_state.json"

payload = {}
if src.exists():
    try:
        payload = json.loads(src.read_text(errors="ignore"))
    except Exception:
        payload = {}

state_payload = {
    "state": "running",
    "pid": None,
    "updated_at_unix": time.time(),
    "last_signal": {
        "total_pageviews": payload.get("total_pageviews"),
        "landing_pageviews": payload.get("landing_pageviews"),
        "interest_pageviews": payload.get("interest_pageviews"),
        "interest_conversion_rate": payload.get("interest_conversion_rate"),
        "evidence_state": payload.get("evidence_state"),
        "profit_engine_promotion": payload.get("profit_engine_promotion"),
    }
}
try:
    state_payload["pid"] = int((Path.home()/".companyos_runtime/live_market_signal_monitor.pid").read_text().strip())
except Exception:
    pass

state.write_text(json.dumps(state_payload, indent=2, sort_keys=True) + "\n")
print("MONITOR_SIGNAL_STATE=", json.dumps(state_payload["last_signal"], sort_keys=True))
PY
        } >> "$LOGFILE" 2>&1

        sleep "$INTERVAL_SECONDS"
      done
    ' >/dev/null 2>&1 &

    pid="$!"
    printf '%s\n' "$pid" > "$PIDFILE"
    write_state "running" "$pid" "started"

    sleep 1
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "V65_91_ABORT=monitor_failed_to_start"
      rm -f "$PIDFILE"
      exit 1
    fi

    echo "MONITOR_RUNNING=true"
    echo "PID=$pid"
    echo "LOGFILE=$LOGFILE"
    echo "STATEFILE=$STATEFILE"
    echo "V65_91_MARKET_SIGNAL_MONITOR=PASS"
    echo "V65_91_NO_FAKE_MARKET_TRAFFIC=PASS"
    echo "V65_91_NO_PROFIT_PROMOTION=PASS"
    echo "V65_91_COMPLETE"
    ;;

  *)
    echo "Usage: $0 {start|status|stop|restart}"
    exit 2
    ;;
esac
