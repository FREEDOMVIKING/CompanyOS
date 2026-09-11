from pathlib import Path
import shutil,time,stat
ROOT=Path.home()/"companyos";SRC=Path(__file__).resolve().parent;D=ROOT/"dashboard";D.mkdir(parents=True,exist_ok=True);stamp=str(int(time.time()))
for name in ["autonomy_activity_ledger_server.py","autonomy_activity_ledger.html"]:
    s=SRC/"dashboard"/name;d=D/name
    if d.exists():
        b=d.with_name(d.name+".bak."+stamp);shutil.copy2(d,b);print("BACKUP:",b)
    shutil.copy2(s,d);print("INSTALLED:",d)
launcher=D/"autonomy_activity_ledger_start.sh"
launcher.write_text("""#!/data/data/com.termux/files/usr/bin/bash
set -e
cd "$HOME/companyos"
export PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos"
mkdir -p .companyos_runtime
PIDFILE=.companyos_runtime/autonomy_activity_ledger.pid
LOGFILE=.companyos_runtime/autonomy_activity_ledger.log
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
 echo "AUTONOMY_ACTIVITY_LEDGER_ALREADY_RUNNING pid=$(cat "$PIDFILE")"
 echo "Open: http://127.0.0.1:8768"
 exit 0
fi
nohup python dashboard/autonomy_activity_ledger_server.py >> "$LOGFILE" 2>&1 &
PID=$!
echo "$PID" > "$PIDFILE"
sleep 1
if kill -0 "$PID" 2>/dev/null; then
 echo "AUTONOMY_ACTIVITY_LEDGER_STARTED pid=$PID"
 echo "Open: http://127.0.0.1:8768"
else
 echo "AUTONOMY_ACTIVITY_LEDGER_START_FAILED"
 tail -n 100 "$LOGFILE" || true
 exit 1
fi
""")
launcher.chmod(launcher.stat().st_mode|stat.S_IXUSR)
for name in ["index.html","master_control.html","venture_progress_v2.html"]:
    p=D/name
    if not p.exists(): continue
    t=p.read_text(errors="ignore")
    if "127.0.0.1:8768" not in t:
        link='<a href="http://127.0.0.1:8768" style="position:fixed;right:14px;top:14px;z-index:99999;padding:10px 13px;border-radius:12px;background:#202733;color:white;text-decoration:none;font-family:system-ui;font-weight:700">📒 Activity Ledger</a>'
        b=p.with_name(p.name+".bak."+stamp);shutil.copy2(p,b)
        t=t.replace("</body>",link+"\\n</body>") if "</body>" in t else t+"\\n"+link
        p.write_text(t);print("LINK_ADDED:",p)
print("AUTONOMY_ACTIVITY_LEDGER_INSTALL: PASS")
print("BOT_RUNTIME_MODIFIED: NO")
print("WALLET_CONFIG_MODIFIED: NO")
