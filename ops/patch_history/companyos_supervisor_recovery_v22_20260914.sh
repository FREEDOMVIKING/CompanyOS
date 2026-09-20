#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
cd "$HOME/companyos"
echo "===== V22 SAFE ROLLBACK + RECOVERY ====="
BK="$(find "$HOME/companyos/.companyos_backups" -maxdepth 1 -type d -name 'stale_pid_recovery_v21_*' 2>/dev/null | sort | tail -n 1)"
[ -n "${BK:-}" ] && [ -f "$BK/runtime_control.py" ] || { echo "ERROR: V21 backup not found"; exit 1; }
cp -f "$BK/runtime_control.py" companyos/runtime/runtime_control.py
python -m py_compile companyos/runtime/runtime_control.py
echo "RESTORED_RUNTIME_CONTROL=PASS"
python - <<'PY'
import json,os
from pathlib import Path
rt=Path(".companyos_runtime"); pf=rt/"service_supervisor.pid"; sf=rt/"service_supervisor_state.json"
def alive(pid):
    try:
        pid=int(pid)
        if pid<=1:return False
        os.kill(pid,0); return True
    except ProcessLookupError:return False
    except PermissionError:return True
    except Exception:return False
try: pid=int(pf.read_text().strip())
except Exception: pid=None
print("OLD_PID=",pid,"ALIVE=",alive(pid) if pid else False)
if pid and not alive(pid):
    pf.unlink(missing_ok=True); print("STALE_PID_REMOVED=true")
if sf.exists():
    try:d=json.loads(sf.read_text())
    except Exception:d={}
    spid=d.get("supervisor_pid")
    if spid and not alive(spid):
        d["supervisor_pid"]=None; d["supervisor_alive"]=False; d["stop_requested"]=False
        sf.write_text(json.dumps(d,indent=2)+"\n")
        print("STALE_STATE_CLEARED=true")
PY
scripts/companyosctl start || true
sleep 15
python - <<'PY'
import json,os,sys
from pathlib import Path
p=Path(".companyos_runtime/service_supervisor_state.json")
d=json.loads(p.read_text()) if p.exists() else {}
pid=d.get("supervisor_pid")
try: os.kill(int(pid),0); alive=True
except Exception: alive=False
print("SUPERVISOR_PID=",pid)
print("SUPERVISOR_ALIVE=",alive)
print("STOP_REQUESTED=",d.get("stop_requested"))
services=d.get("services") or {}
print("LIVE_SERVICES=",sum(1 for v in services.values() if isinstance(v,dict) and v.get("process_alive")))
print("TOTAL_SERVICES=",len(services))
if not alive: sys.exit(2)
PY
scripts/companyosctl status || true
scripts/companyosctl health || true
echo "COMPANYOS_SUPERVISOR_RECOVERY_V22=PASS"
