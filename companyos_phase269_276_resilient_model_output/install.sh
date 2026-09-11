#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase269_276_resilient_model_output_$STAMP"

echo "=== CompanyOS Phase 269-276 ==="
echo "RESILIENT MODEL OUTPUT + AUTOMATIC CONTRACT RECOVERY"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"

TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

if [ -d "$TARGET/companyos_phase269_276" ]; then
  cp -a "$TARGET/companyos_phase269_276" "$BACKUP/" || true
fi

rm -rf "$TARGET/companyos_phase269_276"
cp -a "$HERE/companyos_phase269_276" "$TARGET/"

cp "$HERE/scripts/patch_autonomous_improver_resilient.py" "$ROOT/scripts/"
cp "$HERE/scripts/phase269_276_verify.py" "$ROOT/scripts/"
cp "$HERE/tests/test_phase269_276.py" "$ROOT/tests/"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase269_276_verify.py
python -m pytest -q tests/test_phase269_276.py --disable-warnings

# Rewire Phase 267 autonomous improver to use resilient generation.
python scripts/patch_autonomous_improver_resilient.py

cat > "$ROOT/PHASE269_276_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase269_276_resilient_model_output","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

echo
echo "PHASE269_276_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "RESILIENT_MODEL_OUTPUT=READY"
echo "AUTONOMOUS_IMPROVER_REWIRED=TRUE"
echo "JSON_RECOVERY=TRUE"
echo "AUTOMATIC_FORMAT_RETRY=TRUE"
echo "Backup: $BACKUP"
