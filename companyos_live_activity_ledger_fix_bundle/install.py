from pathlib import Path
import shutil, time, stat, subprocess, os, signal

ROOT = Path.home() / "companyos"
SRC = Path(__file__).resolve().parent
DASH = ROOT / "dashboard"
DASH.mkdir(parents=True, exist_ok=True)
stamp = str(int(time.time()))

for name in ["autonomy_activity_ledger_server.py", "autonomy_activity_ledger.html"]:
    src = SRC / "dashboard" / name
    dst = DASH / name
    if dst.exists():
        backup = dst.with_name(dst.name + ".bak.live_ledger." + stamp)
        shutil.copy2(dst, backup)
        print("BACKUP:", backup)
    shutil.copy2(src, dst)
    print("INSTALLED:", dst)

start = DASH / "autonomy_activity_ledger_start.sh"
if start.exists():
    shutil.copy2(start, start.with_name(start.name + ".bak.live_ledger." + stamp))

start.write_text("""#!/data/data/com.termux/files/usr/bin/bash
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
""")
start.chmod(start.stat().st_mode | stat.S_IXUSR)

print("LIVE_AUTONOMY_ACTIVITY_LEDGER_INSTALL: PASS")
print("PORT: 8768")
print("BOT_RUNTIME_LOGIC_MODIFIED: NO")
print("WALLET_CONFIG_MODIFIED: NO")
print("FINANCIAL_LIMITS_MODIFIED: NO")
