#!/data/data/com.termux/files/usr/bin/bash
set -e
cd "$HOME/companyos"
export PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos"
mkdir -p .companyos_runtime
PIDFILE=.companyos_runtime/venture_progress_v2.pid
LOGFILE=.companyos_runtime/venture_progress_v2.log

# Stop the old V1 tracker only; do not touch CompanyOS runtime or dashboards.
if [ -f .companyos_runtime/venture_progress.pid ]; then
  OLD="$(cat .companyos_runtime/venture_progress.pid 2>/dev/null || true)"
  if [ -n "$OLD" ] && kill -0 "$OLD" 2>/dev/null; then
    kill "$OLD" 2>/dev/null || true
    sleep 1
  fi
  rm -f .companyos_runtime/venture_progress.pid
fi

# Clear any stale V2 process on the same port.
if [ -f "$PIDFILE" ]; then
  P="$(cat "$PIDFILE" 2>/dev/null || true)"
  if [ -n "$P" ] && kill -0 "$P" 2>/dev/null; then
    kill "$P" 2>/dev/null || true
    sleep 1
  fi
  rm -f "$PIDFILE"
fi

nohup python dashboard/venture_progress_v2_server.py >> "$LOGFILE" 2>&1 &
PID=$!
echo "$PID" > "$PIDFILE"
sleep 1
if kill -0 "$PID" 2>/dev/null; then
  echo "VENTURE_PROGRESS_V2_STARTED pid=$PID"
  echo "Open: http://127.0.0.1:8767"
else
  echo "VENTURE_PROGRESS_V2_START_FAILED"
  tail -n 100 "$LOGFILE" || true
  exit 1
fi
