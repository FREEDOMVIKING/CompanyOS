#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase777_792_multi_provider_research_execution_$STAMP"

echo "=== CompanyOS Phase 777-792 ==="
echo "AUTONOMOUS MULTI-PROVIDER RESEARCH EXECUTION + EVIDENCE COLLECTION"
[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"; [ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase777_792"
cp -a "$HERE/companyos_phase777_792" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase777_792.py" "$ROOT/tests/"
chmod +x "$ROOT/scripts/run_multi_provider_research_demo.py" "$ROOT/scripts/phase777_792_verify.py"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase777_792_verify.py
python -m pytest -q tests/test_phase777_792.py --disable-warnings

echo
echo "PHASE777_792_INSTALL_OK"
echo "PROVIDER_ADAPTERS=READY"
echo "PROVIDER_DISPATCH=READY"
echo "QUERY_TRANSFORMATION=READY"
echo "FALLBACK_CHAIN=READY"
echo "MULTI_PROVIDER_EVIDENCE_COLLECTION=READY"
echo "EVIDENCE_MERGE_DEDUPE=READY"
echo "PROVIDER_ERROR_NORMALIZATION=READY"
echo "FAILOVER_SEQUENCE=READY"
echo "SOURCE_QUOTA_BALANCING=READY"
echo "DIVERSITY_GATE=READY"
echo "COMPLETION_POLICY=READY"
echo "PARTIAL_RESULT_PRESERVATION=READY"
echo "PROVIDER_EXECUTION_AUDIT=READY"
echo "RESEARCH_PACKET_ASSEMBLY=READY"
echo "LIFECYCLE_EVIDENCE_OUTPUT=READY"
echo "CEO_MULTI_PROVIDER_BRIDGE=READY"
echo "Backup: $BACKUP"
