#!/data/data/com.termux/files/usr/bin/bash
set -e
cd "$HOME/companyos"
export PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos"
mkdir -p .companyos_runtime
PIDFILE=.companyos_runtime/master_control.pid
LOGFILE=.companyos_runtime/master_control.log
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "MASTER_CONTROL_ALREADY_RUNNING pid=$(cat "$PIDFILE")"
  echo "Open: http://127.0.0.1:8766"
  exit 0
fi
nohup python dashboard/master_control_server.py >> "$LOGFILE" 2>&1 &
PID=$!
echo "$PID" > "$PIDFILE"
sleep 1
if kill -0 "$PID" 2>/dev/null; then
  echo "MASTER_CONTROL_STARTED pid=$PID"
  echo "Open: http://127.0.0.1:8766"
else
  echo "MASTER_CONTROL_START_FAILED"
  tail -n 80 "$LOGFILE" || true
  exit 1
fi
