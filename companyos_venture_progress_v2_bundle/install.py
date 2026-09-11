from pathlib import Path
import shutil, time, stat

ROOT=Path.home()/"companyos"
SRC=Path(__file__).resolve().parent
D=ROOT/"dashboard"
D.mkdir(parents=True,exist_ok=True)
stamp=str(int(time.time()))

for name in ["venture_progress_v2_server.py","venture_progress_v2.html"]:
    s=SRC/"dashboard"/name
    d=D/name
    if d.exists():
        b=d.with_name(d.name+".bak."+stamp)
        shutil.copy2(d,b)
        print("BACKUP:",b)
    shutil.copy2(s,d)
    print("INSTALLED:",d)

launcher=D/"venture_progress_v2_start.sh"
launcher.write_text("""#!/data/data/com.termux/files/usr/bin/bash
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
""")
launcher.chmod(launcher.stat().st_mode|stat.S_IXUSR)

# Update dashboard links to point to V2, preserving backups.
for name in ["index.html","master_control.html"]:
    p=D/name
    if not p.exists():
        continue
    t=p.read_text(errors="ignore")
    b=p.with_name(p.name+".bak."+stamp)
    shutil.copy2(p,b)
    # existing 8767 links already work, but label them V2 if present
    t=t.replace("Venture Progress Tracker</a>","Venture Progress Tracker V2</a>")
    t=t.replace("📈 Venture Progress Tracker</a>","📈 Venture Progress Tracker V2</a>")
    if "127.0.0.1:8767" not in t:
        link='<a href="http://127.0.0.1:8767" style="position:fixed;left:14px;bottom:14px;z-index:99999;padding:12px 15px;border-radius:12px;background:#202733;color:white;text-decoration:none;font-family:system-ui;font-weight:700">📈 Venture Progress Tracker V2</a>'
        t=t.replace("</body>",link+"\\n</body>") if "</body>" in t else t+"\\n"+link
    p.write_text(t)
    print("LINK_UPDATED:",p)
    print("BACKUP:",b)

print("VENTURE_PROGRESS_V2_INSTALL: PASS")
print("BOT_RUNTIME_MODIFIED: NO")
print("WALLET_CONFIG_MODIFIED: NO")
print("EXECUTIVE_DASHBOARD_REPLACED: NO")
