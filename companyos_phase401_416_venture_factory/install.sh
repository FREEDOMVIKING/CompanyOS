#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase401_416_venture_factory_$STAMP"

echo "=== CompanyOS Phase 401-416 ==="
echo "VENTURE FACTORY"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase401_416"
cp -a "$HERE/companyos_phase401_416" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase401_416.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/run_venture_factory_demo.py"
chmod +x "$ROOT/scripts/venture_factory_status.py"
chmod +x "$ROOT/scripts/phase401_416_verify.py"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase401_416_verify.py
python -m pytest -q tests/test_phase401_416.py --disable-warnings

cat > "$ROOT/PHASE401_416_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase401_416_venture_factory","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

echo
echo "PHASE401_416_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "VENTURE_FACTORY=READY"
echo "VALIDATION_GATE=ENFORCED"
echo "MVP_SCOPE_CONTROL=READY"
echo "SPECIALIST_DELEGATION=READY"
echo "QUALITY_GATES=READY"
echo "KPI_CONTRACTS=READY"
echo "Backup: $BACKUP"
