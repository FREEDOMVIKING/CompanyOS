#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase253_260_repair_upgrade_$STAMP"

echo "=== CompanyOS Phase 253-260 Repair Upgrade ==="
echo "TARGETED FAILURE-AWARE MODEL REPAIR"

TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"
PKG="$TARGET/companyos_phase253_260"

[ -d "$PKG" ] || { echo "ERROR: Phase253-260 package not found"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/tests"
cp "$PKG/repair_controller.py" "$BACKUP/repair_controller.py"
cp "$PKG/builder_bridge.py" "$BACKUP/builder_bridge.py"

cp "$HERE/patch/repair_controller.py" "$PKG/repair_controller.py"
cp "$HERE/patch/builder_bridge.py" "$PKG/builder_bridge.py"
cp "$HERE/tests/test_repair_upgrade.py" "$ROOT/tests/test_phase253_260_repair_upgrade.py"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python -m py_compile "$PKG/repair_controller.py" "$PKG/builder_bridge.py"
python -m pytest -q tests/test_phase253_260_repair_upgrade.py --disable-warnings

echo
echo "PHASE253_260_REPAIR_UPGRADE_OK"
echo "CURRENT_CODE_INCLUDED_IN_REPAIR_PROMPT=TRUE"
echo "REQUIRED_PACKAGE_LAYOUT_ENFORCED=TRUE"
echo "FAILURE_AWARE_REPAIR=TRUE"
echo "Backup: $BACKUP"
