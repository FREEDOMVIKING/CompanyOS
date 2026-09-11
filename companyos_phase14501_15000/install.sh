#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase14501_15000_cicd_$STAMP"

echo "=== CompanyOS Phase 14501-15000 ==="
echo "AUTONOMOUS CI/CD + RELEASE ENGINEERING"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests" "$ROOT/.github/workflows"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"
cp "$HERE/.github/workflows/"* "$ROOT/.github/workflows/"

chmod +x "$ROOT/scripts/phase14501_15000_verify.py"
chmod +x "$ROOT/scripts/run_phase15000_cicd_demo.py"
chmod +x "$ROOT/scripts/companyos_cicd.sh"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python scripts/phase14501_15000_verify.py
python -m pytest -q tests/test_phase14501_15000.py --disable-warnings

echo
echo "PHASE14501_15000_INSTALL_OK"
echo "PIPELINE_GRAPH=READY"
echo "QUALITY_GATE=READY"
echo "SECURITY_GATE=READY"
echo "ARTIFACT_BUILDER=READY"
echo "RELEASE_MANIFEST=READY"
echo "STAGING_VALIDATOR=READY"
echo "DEPLOYMENT_GATE=READY"
echo "POSTDEPLOY_VERIFIER=READY"
echo "ROLLBACK_POLICY=READY"
echo "RELEASE_LEDGER=READY"
echo "PERSISTENT_PIPELINE_STATE=READY"
echo "PIPELINE_AUDIT=READY"
echo "CEO_CICD_CONTROLLER=READY"
echo "GITHUB_CI_WORKFLOW=READY"
echo "GITHUB_RELEASE_WORKFLOW=READY"
echo "Backup: $BACKUP"
