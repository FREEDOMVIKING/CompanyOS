#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase6001_6500_hardening_$STAMP"

echo "=== CompanyOS Phase 6001-6500 ==="
echo "PRODUCTION HARDENING + OBSERVABILITY"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/phase6001_6500_verify.py"
chmod +x "$ROOT/scripts/run_phase6500_hardening_demo.py"
chmod +x "$ROOT/scripts/companyos_hardening.sh"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python scripts/phase6001_6500_verify.py
python -m pytest -q tests/test_phase6001_6500.py --disable-warnings

echo
echo "PHASE6001_6500_INSTALL_OK"
echo "HEALTH_MATRIX=READY"
echo "SLO_ENGINE=READY"
echo "INCIDENT_MANAGER=READY"
echo "BACKUP_MANAGER=READY"
echo "INTEGRITY_CHECKER=READY"
echo "CONFIG_VALIDATOR=READY"
echo "SECRET_REFERENCE_AUDIT=READY"
echo "ROLLBACK_MANAGER=READY"
echo "CHAOS_PROBE=READY"
echo "CAPACITY_PLANNER=READY"
echo "OBSERVABILITY_SNAPSHOT=READY"
echo "RELEASE_GATE=READY"
echo "PERSISTENT_HARDENING_STATE=READY"
echo "HARDENING_AUDIT=READY"
echo "PRODUCTION_HARDENING_CONTROLLER=READY"
echo "Backup: $BACKUP"
