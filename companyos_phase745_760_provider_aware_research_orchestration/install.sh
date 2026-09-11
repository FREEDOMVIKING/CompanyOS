#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase745_760_provider_aware_research_orchestration_$STAMP"

echo "=== CompanyOS Phase 745-760 ==="
echo "PROVIDER-AWARE RESEARCH ORCHESTRATION + EVIDENCE QUALITY CONTROL"
[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"; [ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase745_760"
cp -a "$HERE/companyos_phase745_760" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase745_760.py" "$ROOT/tests/"
chmod +x "$ROOT/scripts/run_research_quality_demo.py" "$ROOT/scripts/phase745_760_verify.py"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase745_760_verify.py
python -m pytest -q tests/test_phase745_760.py --disable-warnings

echo
echo "PHASE745_760_INSTALL_OK"
echo "PROVIDER_HEALTH_SCORING=READY"
echo "COOLDOWN_AWARE_PROVIDER_SELECTION=READY"
echo "SOURCE_DIVERSIFICATION=READY"
echo "QUERY_ROUTING=READY"
echo "EVIDENCE_DEDUPLICATION=READY"
echo "FRESHNESS_SCORING=READY"
echo "CREDIBILITY_WEIGHTING=READY"
echo "EVIDENCE_COMPLETENESS=READY"
echo "CONTRADICTION_DETECTION=READY"
echo "WEAK_SIGNAL_FILTERING=READY"
echo "RESEARCH_STOP_POLICY=READY"
echo "RETRY_BUDGETS=READY"
echo "EVIDENCE_CONFIDENCE=READY"
echo "RESEARCH_NORMALIZATION=READY"
echo "CEO_RESEARCH_SUMMARY=READY"
echo "Backup: $BACKUP"
