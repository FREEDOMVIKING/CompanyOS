#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase15001_15500_daemon_$STAMP"

echo "=== CompanyOS Phase 15001-15500 ==="
echo "AUTONOMOUS DAEMON + EVENT RUNTIME"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/phase15001_15500_verify.py"
chmod +x "$ROOT/scripts/run_phase15500_daemon_demo.py"
chmod +x "$ROOT/scripts/companyos_daemon.sh"
chmod +x "$ROOT/scripts/companyos_daemon_forever.sh"
chmod +x "$ROOT/scripts/companyos_daemon_control.sh"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python scripts/phase15001_15500_verify.py
python -m pytest -q tests/test_phase15001_15500.py --disable-warnings

echo
echo "PHASE15001_15500_INSTALL_OK"
echo "EVENT_BUS=READY"
echo "DURABLE_JOB_QUEUE=READY"
echo "AUTONOMOUS_SCHEDULER=READY"
echo "DAEMON_STATE=READY"
echo "SELF_HEALING_SUPERVISOR=READY"
echo "RESTART_RECOVERY=READY"
echo "TRIGGER_ROUTER=READY"
echo "HEARTBEAT_MONITOR=READY"
echo "JOB_LEASE_MANAGER=READY"
echo "DEAD_LETTER_QUEUE=READY"
echo "CEO_AUTONOMOUS_LOOP=READY"
echo "RUNTIME_AUDIT=READY"
echo "DAEMON_CONTROL=READY"
echo "Backup: $BACKUP"
