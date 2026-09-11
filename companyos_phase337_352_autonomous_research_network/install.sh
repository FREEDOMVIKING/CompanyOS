#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase337_352_autonomous_research_network_$STAMP"

echo "=== CompanyOS Phase 337-352 ==="
echo "AUTONOMOUS RESEARCH NETWORK + CEO DECISION INPUT"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

[ -d "$TARGET/companyos_phase337_352" ] && cp -a "$TARGET/companyos_phase337_352" "$BACKUP/" || true

rm -rf "$TARGET/companyos_phase337_352"
cp -a "$HERE/companyos_phase337_352" "$TARGET/"
cp "$HERE/scripts/install_starter_research_network.py" "$ROOT/scripts/"
cp "$HERE/scripts/run_autonomous_research_cycle.py" "$ROOT/scripts/"
cp "$HERE/scripts/research_network_status.py" "$ROOT/scripts/"
cp "$HERE/scripts/phase337_352_verify.py" "$ROOT/scripts/"
cp "$HERE/tests/test_phase337_352.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/install_starter_research_network.py"
chmod +x "$ROOT/scripts/run_autonomous_research_cycle.py"
chmod +x "$ROOT/scripts/research_network_status.py"

cat > "$ROOT/PHASE337_352_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase337_352_autonomous_research_network","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase337_352_verify.py
python -m pytest -q tests/test_phase337_352.py --disable-warnings
python scripts/install_starter_research_network.py

echo
echo "PHASE337_352_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "AUTONOMOUS_RESEARCH_NETWORK=READY"
echo "STARTER_SOURCE_REGISTRY=READY"
echo "QUALITY_GATING=TRUE"
echo "MARKET_GAP_DETECTION=TRUE"
echo "CEO_DECISION_INPUT=READY"
echo "Backup: $BACKUP"
