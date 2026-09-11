#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase737_744_provider_rate_limit_recovery_$STAMP"
echo "=== CompanyOS Phase 737-744 ==="
echo "PROVIDER RATE-LIMIT RECOVERY + MISSION RETRY RESILIENCE"
[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }
mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"; [ -d "$ROOT/src" ] && TARGET="$ROOT/src"
RUNTIME_FILE="$TARGET/companyos_phase705_720/persistent_runtime.py"
[ -f "$RUNTIME_FILE" ] && cp "$RUNTIME_FILE" "$BACKUP/persistent_runtime.py.before"
rm -rf "$TARGET/companyos_phase737_744"
cp -a "$HERE/companyos_phase737_744" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase737_744.py" "$ROOT/tests/"
chmod +x "$ROOT/scripts/patch_unified_runtime_resilience.py" "$ROOT/scripts/phase737_744_verify.py"
cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"; else export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"; fi
python scripts/phase737_744_verify.py
python -m pytest -q tests/test_phase737_744.py --disable-warnings
python scripts/patch_unified_runtime_resilience.py
python -m py_compile "$RUNTIME_FILE"
echo
echo "PHASE737_744_INSTALL_OK"
echo "RATE_LIMIT_DETECTION=READY"
echo "PROVIDER_COOLDOWNS=READY"
echo "BOUNDED_BACKOFF=READY"
echo "FALLBACK_PROVIDER_SELECTION=READY"
echo "MISSION_RESCHEDULING=READY"
echo "TRANSIENT_PROVIDER_FAILURES_DO_NOT_INCREMENT_HARD_FAILURE_COUNT=READY"
echo "UNIFIED_RUNTIME_PATCH=APPLIED"
echo "Backup: $BACKUP"
