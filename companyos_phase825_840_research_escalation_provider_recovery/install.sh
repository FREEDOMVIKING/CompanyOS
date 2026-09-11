#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase825_840_research_escalation_provider_recovery_$STAMP"

echo "=== CompanyOS Phase 825-840 ==="
echo "AUTONOMOUS RESEARCH ESCALATION + PROVIDER FAILURE RECOVERY"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase825_840"
cp -a "$HERE/companyos_phase825_840" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase825_840.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/run_research_escalation_demo.py"
chmod +x "$ROOT/scripts/phase825_840_verify.py"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase825_840_verify.py
python -m pytest -q tests/test_phase825_840.py --disable-warnings

echo
echo "PHASE825_840_INSTALL_OK"
echo "FAILURE_CLASSIFICATION=READY"
echo "PROVIDER_ESCALATION_POLICY=READY"
echo "QUERY_REFORMULATION=READY"
echo "EVIDENCE_GAP_ANALYSIS=READY"
echo "PROVIDER_RETRY_BUDGETS=READY"
echo "ADAPTIVE_BACKOFF=READY"
echo "ESCALATION_STATE=READY"
echo "PROVIDER_CHAIN_BUILDER=READY"
echo "EVIDENCE_ACCUMULATION=READY"
echo "CONFIDENCE_PROGRESS=READY"
echo "PROMOTION_THRESHOLD=READY"
echo "BOUNDED_DEFER_POLICY=READY"
echo "RESEARCH_ESCALATION_AUDIT=READY"
echo "CEO_RESEARCH_ESCALATION_BRIDGE=READY"
echo "Backup: $BACKUP"
