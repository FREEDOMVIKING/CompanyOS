#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase385_400_validation_experiment_engine_$STAMP"

echo "=== CompanyOS Phase 385-400 ==="
echo "VALIDATION EXPERIMENT ENGINE"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase385_400"
cp -a "$HERE/companyos_phase385_400" "$TARGET/"
cp "$HERE/scripts/run_validation_demo.py" "$ROOT/scripts/"
cp "$HERE/scripts/validation_status.py" "$ROOT/scripts/"
cp "$HERE/scripts/phase385_400_verify.py" "$ROOT/scripts/"
cp "$HERE/tests/test_phase385_400.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/run_validation_demo.py"
chmod +x "$ROOT/scripts/validation_status.py"

cat > "$ROOT/PHASE385_400_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase385_400_validation_experiment_engine","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase385_400_verify.py
python -m pytest -q tests/test_phase385_400.py --disable-warnings

echo
echo "PHASE385_400_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "VALIDATION_EXPERIMENT_ENGINE=READY"
echo "HYPOTHESIS_ENGINE=READY"
echo "GO_NOGO_ENGINE=READY"
echo "FULL_PRODUCT_BEFORE_VALIDATION=FALSE"
echo "Backup: $BACKUP"
