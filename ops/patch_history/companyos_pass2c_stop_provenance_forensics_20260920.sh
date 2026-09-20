#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
cd "$ROOT" || exit 1
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS PASS 2C STOP-PROVENANCE FORENSICS ====="
echo "MODE=READ_ONLY"
echo "NOTE=NO_RUNTIME_START_OR_STOP"
echo "NOTE=NO_EMAIL_SEND"
echo "NOTE=NO_FINANCIAL_ACTION"
echo "NOTE=NO_DEPLOYMENT"
echo

echo "===== CURRENT CONTROL MARKERS ====="
for f in "$RT/SUPERVISOR_STOP" "$RT/STOP_CONTINUOUS" "$RT/continuous_goal_runtime.stop"; do
  echo "--- $f ---"
  if [ -e "$f" ]; then
    stat "$f" 2>/dev/null || ls -l "$f"
    printf 'contents='
    head -c 300 "$f" 2>/dev/null || true
    echo
  else
    echo "exists=false"
  fi
done

echo
echo "===== CURRENT CANONICAL HEALTH ====="
python - <<'PY'
from pathlib import Path
import json
from companyos.runtime.runtime_control import UnifiedRuntimeControl
c=UnifiedRuntimeControl(Path.home()/"companyos")
h=c.health()
print(json.dumps({
    "healthy":h.get("healthy"),
    "issues":h.get("issues"),
    "supervisor_pid":h.get("supervisor_pid"),
    "supervisor_alive":h.get("supervisor_alive"),
    "stop_requested":h.get("stop_requested"),
    "state_age_seconds":h.get("state_age_seconds"),
    "expected_services_present":h.get("expected_services_present"),
    "not_running":[
        name for name,row in (h.get("services") or {}).items()
        if not row.get("running") or not row.get("process_alive")
    ],
},indent=2,sort_keys=True))
PY

echo
echo "===== COMPANYOS PROCESSES ====="
pgrep -af 'companyos|CompanyOS' || true

echo
echo "===== RUNTIME CONTROL LOG: STOP/START EVENTS ====="
if [ -f "$RT/runtime_control.log" ]; then
  grep -En 'STOP requested|START requested|STALE|FOREIGN|already|recover|restart' "$RT/runtime_control.log" | tail -n 160 || true
else
  echo "runtime_control.log missing"
fi

echo
echo "===== SUPERVISOR LOG: LAST 220 CONTROL EVENTS ====="
if [ -f "$RT/service_supervisor.log" ]; then
  grep -En 'SUPERVISOR_(START|STOP|ALREADY_RUNNING)|SIGNAL|IGNORED_STALE_STOP_REQUEST|START service=|EXIT service=' "$RT/service_supervisor.log" | tail -n 220 || true
else
  echo "service_supervisor.log missing"
fi

echo
echo "===== SOURCE REFERENCES TO SUPERVISOR_STOP / REQUEST_STOP ====="
grep -RInE \
  --exclude-dir=.git \
  --exclude='*.pyc' \
  --exclude='*.log' \
  --exclude='*.json' \
  'SUPERVISOR_STOP|request_stop\(|stop_path\.write_text|companyosctl[[:space:]]+stop|companyos_launchctl[[:space:]]+stop' \
  companyos scripts tests *.sh 2>/dev/null | head -n 300 || true

echo
echo "===== RECENT SHELL HISTORY REFERENCES TO STOP COMMANDS ====="
if [ -f "$HOME/.bash_history" ]; then
  grep -En 'companyosctl stop|companyos_launchctl stop|SUPERVISOR_STOP' "$HOME/.bash_history" | tail -n 80 || true
fi

echo
echo "===== GIT STATUS ====="
git --no-pager status --short
echo "HEAD=$(git rev-parse HEAD)"
echo "BRANCH=$(git branch --show-current)"

echo
echo "COMPANYOS_PASS_2C_STOP_PROVENANCE_FORENSICS=COMPLETE"
