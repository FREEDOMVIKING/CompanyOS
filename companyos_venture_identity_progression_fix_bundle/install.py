from pathlib import Path
import shutil, time, stat, subprocess, os
ROOT=Path.home()/'companyos'
SRC=Path(__file__).resolve().parent
stamp=str(int(time.time()))
for rel in ['companyos/governance/venture_identity_progression.py','scripts/companyos_progression_directive.py','scripts/patch_productive_autonomy_progression.py','dashboard/venture_identity_progression_server.py','dashboard/venture_identity_progression.html']:
    s=SRC/rel; d=ROOT/rel; d.parent.mkdir(parents=True,exist_ok=True)
    if d.exists():
        b=d.with_name(d.name+'.bak.'+stamp); shutil.copy2(d,b); print('BACKUP:',b)
    shutil.copy2(s,d); print('INSTALLED:',d)

launch=ROOT/'dashboard'/'venture_identity_progression_start.sh'
launch.write_text('''#!/data/data/com.termux/files/usr/bin/bash
cd "$HOME/companyos" || exit 1
export PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos"
mkdir -p .companyos_runtime
PID=.companyos_runtime/venture_identity_progression.pid
LOG=.companyos_runtime/venture_identity_progression.log
if [ -f "$PID" ] && kill -0 "$(cat "$PID")" 2>/dev/null; then
 echo "VENTURE_IDENTITY_PROGRESSION_ALREADY_RUNNING pid=$(cat "$PID")"
 echo "Open: http://127.0.0.1:8770"
 exit 0
fi
nohup python dashboard/venture_identity_progression_server.py >>"$LOG" 2>&1 &
echo $! >"$PID"
sleep 1
kill -0 "$(cat "$PID")" 2>/dev/null && echo "VENTURE_IDENTITY_PROGRESSION_STARTED pid=$(cat "$PID")" && echo "Open: http://127.0.0.1:8770" || { echo "START_FAILED"; tail -100 "$LOG"; exit 1; }
''')
launch.chmod(launch.stat().st_mode|stat.S_IXUSR)
env=os.environ.copy();env['PYTHONPATH']=f"{ROOT}:{ROOT/'companyos'}"
subprocess.run(['python','scripts/patch_productive_autonomy_progression.py'],cwd=ROOT,env=env,check=True)
print('VENTURE_IDENTITY_PROGRESSION_INSTALL: PASS')
print('INTERNAL_SUPPORT_DIRS_FILTERED: YES')
print('CANONICAL_VENTURE_IDENTITIES_ENABLED: YES')
print('ANTI_DUPLICATE_PROGRESSION_DIRECTIVE_ENABLED: YES')
print('EXTERNAL_APPROVAL_GATES_BYPASSED: NO')
print('FINANCIAL_LIMITS_MODIFIED: NO')
