#!/data/data/com.termux/files/usr/bin/bash
set -e
cd "$HOME/companyos"
export PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos"
mkdir -p .companyos_runtime
PIDFILE=.companyos_runtime/autonomy_activity_ledger.pid
LOGFILE=.companyos_runtime/autonomy_activity_ledger.log

if [ -f "$PIDFILE" ]; then
  OLD="$(cat "$PIDFILE" 2>/dev/null || true)"
  if [ -n "$OLD" ] && kill -0 "$OLD" 2>/dev/null; then
    kill "$OLD" 2>/dev/null || true
    sleep 1
  fi
fi

pkill -f 'dashboard/autonomy_activity_ledger_server.py' 2>/dev/null || true
sleep 1

nohup python dashboard/autonomy_activity_ledger_server.py >> "$LOGFILE" 2>&1 &
PID=$!
echo "$PID" > "$PIDFILE"
sleep 1

if kill -0 "$PID" 2>/dev/null; then
  echo "LIVE_AUTONOMY_ACTIVITY_LEDGER_STARTED pid=$PID"
  echo "Open: http://127.0.0.1:8768"
else
  echo "LIVE_AUTONOMY_ACTIVITY_LEDGER_START_FAILED"
  tail -n 120 "$LOGFILE" || true
  exit 1
fi
