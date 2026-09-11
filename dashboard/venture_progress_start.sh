#!/data/data/com.termux/files/usr/bin/bash
set -e
cd "$HOME/companyos"
export PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos"
mkdir -p .companyos_runtime
PIDFILE=.companyos_runtime/venture_progress.pid
LOGFILE=.companyos_runtime/venture_progress.log
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
 echo "VENTURE_PROGRESS_ALREADY_RUNNING pid=$(cat "$PIDFILE")"
 echo "Open: http://127.0.0.1:8767"
 exit 0
fi
nohup python dashboard/venture_progress_server.py >> "$LOGFILE" 2>&1 &
PID=$!
echo "$PID" > "$PIDFILE"
sleep 1
if kill -0 "$PID" 2>/dev/null; then
 echo "VENTURE_PROGRESS_STARTED pid=$PID"
 echo "Open: http://127.0.0.1:8767"
else
 echo "VENTURE_PROGRESS_START_FAILED"
 tail -n 80 "$LOGFILE" || true
 exit 1
fi
