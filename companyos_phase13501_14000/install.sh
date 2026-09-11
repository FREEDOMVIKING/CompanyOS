#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase13501_14000_product_$STAMP"

echo "=== CompanyOS Phase 13501-14000 ==="
echo "AUTONOMOUS PRODUCT + INNOVATION COMMAND"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/phase13501_14000_verify.py"
chmod +x "$ROOT/scripts/run_phase14000_product_demo.py"
chmod +x "$ROOT/scripts/companyos_product.sh"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python scripts/phase13501_14000_verify.py
python -m pytest -q tests/test_phase13501_14000.py --disable-warnings

echo
echo "PHASE13501_14000_INSTALL_OK"
echo "PROBLEM_SIGNAL_ENGINE=READY"
echo "PRODUCT_ROADMAP_ENGINE=READY"
echo "FEATURE_SCORING_ENGINE=READY"
echo "PROTOTYPE_PLANNER=READY"
echo "PRODUCT_VALIDATION_ENGINE=READY"
echo "RELEASE_PLANNER=READY"
echo "PRODUCT_QUALITY_GATE=READY"
echo "ADOPTION_ENGINE=READY"
echo "PRODUCT_ANALYTICS_ENGINE=READY"
echo "INNOVATION_PORTFOLIO_ENGINE=READY"
echo "PRODUCT_AUTHORITY_BOUNDARY=READY"
echo "PERSISTENT_PRODUCT_OPS_STATE=READY"
echo "PRODUCT_OPS_AUDIT=READY"
echo "CEO_PRODUCT_OPS_CONTROLLER=READY"
echo "Backup: $BACKUP"
