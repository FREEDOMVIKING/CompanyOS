from pathlib import Path
import shutil, time, stat
ROOT=Path.home()/"companyos"; SRC=Path(__file__).resolve().parent; D=ROOT/"dashboard"
D.mkdir(parents=True,exist_ok=True); stamp=str(int(time.time()))
for name in ["venture_progress_server.py","venture_progress.html"]:
    s=SRC/"dashboard"/name; d=D/name
    if d.exists():
        b=d.with_name(d.name+".bak."+stamp); shutil.copy2(d,b); print("BACKUP:",b)
    shutil.copy2(s,d); print("INSTALLED:",d)

launcher=D/"venture_progress_start.sh"
launcher.write_text("""#!/data/data/com.termux/files/usr/bin/bash
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
""")
launcher.chmod(launcher.stat().st_mode|stat.S_IXUSR)

# Add links to both existing dashboards if present.
for name in ["index.html","master_control.html"]:
    p=D/name
    if not p.exists(): continue
    t=p.read_text(errors="ignore")
    if "Venture Progress Tracker" in t: continue
    link='<a href="http://127.0.0.1:8767" style="position:fixed;left:14px;bottom:14px;z-index:99999;padding:12px 15px;border-radius:12px;background:#202733;color:white;text-decoration:none;font-family:system-ui;font-weight:700">📈 Venture Progress Tracker</a>'
    b=p.with_name(p.name+".bak."+stamp); shutil.copy2(p,b)
    t=t.replace("</body>",link+"\\n</body>") if "</body>" in t else t+"\\n"+link
    p.write_text(t); print("LINK_ADDED:",p); print("BACKUP:",b)

print("VENTURE_PROGRESS_INSTALL: PASS")
print("EXISTING_DASHBOARDS_REPLACED: NO")
print("BOT_RUNTIME_MODIFIED: NO")
print("WALLET_CONFIG_MODIFIED: NO")
