#!/data/data/com.termux/files/usr/bin/bash
cd "$HOME/companyos" || exit 1
export PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos"
mkdir -p .companyos_runtime
PID=.companyos_runtime/lifecycle_progress.pid
LOG=.companyos_runtime/lifecycle_progress.log
if [ -f "$PID" ] && kill -0 "$(cat "$PID")" 2>/dev/null; then echo "LIFECYCLE_PROGRESS_ALREADY_RUNNING pid=$(cat "$PID")"; echo "Open: http://127.0.0.1:8769"; exit 0; fi
nohup python dashboard/lifecycle_progress_server.py >>"$LOG" 2>&1 &
echo $! >"$PID";sleep 1
kill -0 "$(cat "$PID")" 2>/dev/null && echo "LIFECYCLE_PROGRESS_STARTED pid=$(cat "$PID")" && echo "Open: http://127.0.0.1:8769" || { echo "START_FAILED";tail -100 "$LOG";exit 1; }
