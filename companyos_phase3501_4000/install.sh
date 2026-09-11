#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase3501_4000_venture_factory_$STAMP"
mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"
chmod +x "$ROOT/scripts/phase3501_4000_verify.py" "$ROOT/scripts/run_phase4000_venture_factory_demo.py" "$ROOT/scripts/companyos_venture_factory.sh"
cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
python scripts/phase3501_4000_verify.py
python -m pytest -q tests/test_phase3501_4000.py --disable-warnings
echo
echo "PHASE3501_4000_INSTALL_OK"
echo "OPPORTUNITY_DISCOVERY=READY"
echo "OPPORTUNITY_RANKING=READY"
echo "VENTURE_SPAWNING=READY"
echo "EXPERIMENT_ENGINE=READY"
echo "UNIT_ECONOMICS=READY"
echo "PORTFOLIO_DECISIONS=READY"
echo "CAPITAL_ALLOCATION=READY"
echo "WORKER_ALLOCATION=READY"
echo "PORTFOLIO_LEARNING=READY"
echo "VENTURE_GUARDRAILS=READY"
echo "AUTONOMOUS_VENTURE_FACTORY=READY"
echo "Backup: $BACKUP"
