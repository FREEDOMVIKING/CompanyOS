#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase213_220_autonomous_self_build_$STAMP"

echo "=== CompanyOS Phase 213-220 ==="
echo "AUTONOMOUS SELF-BUILD PIPELINE"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }
[ -f "$ROOT/PHASE205_212_INSTALLED.json" ] || {
  echo "ERROR: Phase 205-212 self-building runtime foundation is required."
  exit 1
}

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"

TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

if [ -d "$TARGET/companyos_phase213_220" ]; then
  cp -a "$TARGET/companyos_phase213_220" "$BACKUP/" || true
fi

rm -rf "$TARGET/companyos_phase213_220"
cp -a "$HERE/companyos_phase213_220" "$TARGET/"
cp "$HERE/scripts/phase213_220_verify.py" "$ROOT/scripts/"
cp "$HERE/tests/test_phase213_220.py" "$ROOT/tests/"

cat > "$ROOT/PHASE213_220_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase213_220_autonomous_self_build","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high","self_build_pipeline":true}
EOF

cd "$ROOT"

if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase213_220_verify.py

if python -c "import pytest" >/dev/null 2>&1; then
  python -m pytest -q tests/test_phase213_220.py --disable-warnings
fi

echo
echo "PHASE213_220_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "AUTONOMOUS_SELF_BUILD_PIPELINE=TRUE"

if [ -n "${COMPANYOS_CODER_CMD:-}" ]; then
  echo "EXTERNAL_CODER_ADAPTER=CONFIGURED"
else
  echo "EXTERNAL_CODER_ADAPTER=NOT_CONFIGURED"
  echo "NOTE: End-to-end pipeline verified with deterministic scaffold adapter."
  echo "      Configure COMPANYOS_CODER_CMD to connect a real coding/reasoning model."
fi

echo "Backup: $BACKUP"
