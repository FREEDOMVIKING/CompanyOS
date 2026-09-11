from pathlib import Path
import shutil,time,stat
ROOT=Path.home()/"companyos";SRC=Path(__file__).resolve().parent;stamp=str(int(time.time()))
for rel in ["companyos/governance/venture_lifecycle_progression.py","dashboard/lifecycle_progress_server.py","dashboard/lifecycle_progress.html"]:
 s=SRC/rel;d=ROOT/rel;d.parent.mkdir(parents=True,exist_ok=True)
 if d.exists():shutil.copy2(d,d.with_name(d.name+".bak."+stamp))
 shutil.copy2(s,d);print("INSTALLED:",d)
launch=ROOT/"dashboard"/"lifecycle_progress_start.sh"
launch.write_text("""#!/data/data/com.termux/files/usr/bin/bash
cd "$HOME/companyos" || exit 1
export PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos"
mkdir -p .companyos_runtime
PID=.companyos_runtime/lifecycle_progress.pid
LOG=.companyos_runtime/lifecycle_progress.log
if [ -f "$PID" ] && kill -0 "$(cat "$PID")" 2>/dev/null; then echo "LIFECYCLE_PROGRESS_ALREADY_RUNNING pid=$(cat "$PID")"; echo "Open: http://127.0.0.1:8769"; exit 0; fi
nohup python dashboard/lifecycle_progress_server.py >>"$LOG" 2>&1 &
echo $! >"$PID";sleep 1
kill -0 "$(cat "$PID")" 2>/dev/null && echo "LIFECYCLE_PROGRESS_STARTED pid=$(cat "$PID")" && echo "Open: http://127.0.0.1:8769" || { echo "START_FAILED";tail -100 "$LOG";exit 1; }
""");launch.chmod(launch.stat().st_mode|stat.S_IXUSR)
# Add navigation to activity ledger without touching autonomous execution logic.
p=ROOT/"dashboard"/"autonomy_activity_ledger.html"
if p.exists():
 t=p.read_text(errors="ignore")
 if "127.0.0.1:8769" not in t:
  shutil.copy2(p,p.with_name(p.name+".bak."+stamp))
  link=' · <a href="http://127.0.0.1:8769">Lifecycle Progression</a>'
  t=t.replace('</p>',link+'</p>',1);p.write_text(t);print("LINK_ADDED:",p)
print("LIFECYCLE_PROGRESSION_INSTALL: PASS")
print("AUTONOMOUS_EXECUTION_LOGIC_MODIFIED: NO")
print("FINANCIAL_LIMITS_MODIFIED: NO")
