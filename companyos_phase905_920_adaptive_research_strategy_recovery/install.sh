#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase905_920_adaptive_research_strategy_recovery_$STAMP"

echo "=== CompanyOS Phase 905-920 ==="
echo "ADAPTIVE RESEARCH STRATEGY RECOVERY"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }
mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"; [ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase905_920"
cp -a "$HERE/companyos_phase905_920" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase905_920.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/phase905_920_verify.py" "$ROOT/scripts/run_adaptive_recovery_demo.py"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
python scripts/phase905_920_verify.py
python -m pytest -q tests/test_phase905_920.py --disable-warnings

echo
echo "PHASE905_920_INSTALL_OK"
echo "STAGNATION_ROOT_CAUSE=READY"
echo "STRATEGY_REPLANNING=READY"
echo "QUERY_STRATEGY_MUTATION=READY"
echo "PROVIDER_MIX_OPTIMIZATION=READY"
echo "EVIDENCE_NOVELTY_SCORING=READY"
echo "SOURCE_GAP_TARGETING=READY"
echo "SIGNAL_QUALITY_RANKING=READY"
echo "RESEARCH_BUDGET_ALLOCATION=READY"
echo "ADAPTIVE_RETRY_POLICY=READY"
echo "STRATEGY_STATE=READY"
echo "STRATEGY_AUDIT=READY"
echo "REVALIDATION_STRATEGY_BRIDGE=READY"
echo "ANTI_LOOP_GUARD=READY"
echo "ADAPTIVE_RECOVERY_CONTROLLER=READY"
echo "CEO_ADAPTIVE_RECOVERY_BRIDGE=READY"
echo "Backup: $BACKUP"
