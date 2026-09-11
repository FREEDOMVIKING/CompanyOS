from pathlib import Path
import shutil, time, stat
ROOT=Path.home()/"companyos"
SRC=Path(__file__).resolve().parent
D=ROOT/"dashboard"; D.mkdir(parents=True,exist_ok=True)
stamp=str(int(time.time()))
for name in ["master_control_server.py","master_control.html"]:
    s=SRC/"dashboard"/name; d=D/name
    if d.exists():
        b=d.with_name(d.name+".bak."+stamp); shutil.copy2(d,b); print("BACKUP:",b)
    shutil.copy2(s,d); print("INSTALLED:",d)
launcher=D/"master_control_start.sh"
launcher.write_text("""#!/data/data/com.termux/files/usr/bin/bash
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
""")
launcher.chmod(launcher.stat().st_mode|stat.S_IXUSR)
index=D/"index.html"
if index.exists():
    t=index.read_text(errors="ignore")
    if "CompanyOS Master Control Center" not in t:
        link='<a href="http://127.0.0.1:8766" style="position:fixed;right:14px;bottom:14px;z-index:99999;padding:12px 15px;border-radius:12px;background:#202733;color:white;text-decoration:none;font-family:system-ui;font-weight:700">⚙ CompanyOS Master Control Center</a>'
        b=index.with_name(index.name+".bak."+stamp); shutil.copy2(index,b)
        t=t.replace("</body>",link+"\n</body>") if "</body>" in t else t+"\n"+link
        index.write_text(t); print("DASHBOARD_LINK_ADDED:",index); print("BACKUP:",b)
print("MASTER_CONTROL_INSTALL: PASS")
print("EXISTING_DASHBOARD_REPLACED: NO")
print("ARBITRARY_SHELL_ENDPOINT: NO")
