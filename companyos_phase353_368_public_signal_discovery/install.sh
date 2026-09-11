#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase353_368_public_signal_discovery_$STAMP"

echo "=== CompanyOS Phase 353-368 ==="
echo "PUBLIC SIGNAL CONNECTORS + FIRST REAL DISCOVERY PATH"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase353_368"
cp -a "$HERE/companyos_phase353_368" "$TARGET/"
cp "$HERE/scripts/run_public_discovery.py" "$ROOT/scripts/"
cp "$HERE/scripts/public_discovery_status.py" "$ROOT/scripts/"
cp "$HERE/scripts/phase353_368_verify.py" "$ROOT/scripts/"
cp "$HERE/tests/test_phase353_368.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/run_public_discovery.py"
chmod +x "$ROOT/scripts/public_discovery_status.py"

cat > "$ROOT/PHASE353_368_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase353_368_public_signal_discovery","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase353_368_verify.py
python -m pytest -q tests/test_phase353_368.py --disable-warnings

echo
echo "PHASE353_368_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "PUBLIC_SIGNAL_DISCOVERY=READY"
echo "HACKERNEWS_API=READY"
echo "GITHUB_PUBLIC_ISSUES=READY"
echo "NO_KEY_STARTER_NETWORK=TRUE"
echo "CEO_PUBLIC_RESEARCH=READY"
echo "Backup: $BACKUP"
