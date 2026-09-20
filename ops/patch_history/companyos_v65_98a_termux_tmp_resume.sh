#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
CTL="$ROOT/scripts/companyos_drlctl"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

# Termux-safe temp directory. Avoid Android /tmp permission issues.
TERMUX_TMP="${TMPDIR:-${PREFIX:-/data/data/com.termux/files/usr}/tmp}"
mkdir -p "$TERMUX_TMP"
OBS="$TERMUX_TMP/companyos_v65_98_observe.json"

echo "===== COMPANYOS V65.98A TERMUX TMP FIX + RESUME ====="
echo "TERMUX_TMP=$TERMUX_TMP"

echo "===== VERIFY DRL CORE ====="
python -m py_compile companyos/runtime/advanced_drl_controller.py
echo "DRL_MODULE_COMPILE=PASS"

python -m pytest -q tests/test_advanced_drl_controller.py
echo "DRL_TESTS=PASS"

echo "===== COMPLETE LIVE OBSERVATION ====="
python -m companyos.runtime.advanced_drl_controller observe > "$OBS"

python - "$OBS" <<'PY'
import json, sys
from pathlib import Path

p = Path(sys.argv[1])
d = json.loads(p.read_text())
print("OBSERVED_ACTION=", d.get("observed_action"))
print("TRANSITION_ADDED=", d.get("transition_added"))
print("RECOMMENDED_ACTION=", d.get("recommendation",{}).get("recommendation",{}).get("action"))
print("TRAINING=", d.get("training"))
PY

echo "===== START/RESTART PASSIVE DRL LEARNING LOOP ====="
if [ ! -x "$CTL" ]; then
  echo "V65_98A_ABORT=drlctl_missing_or_not_executable"
  exit 1
fi

"$CTL" restart

echo "===== FINAL DRL STATUS ====="
"$CTL" status

echo "===== RECENT DRL LOG ====="
"$CTL" log 40 || true

echo "V65_98A_TERMUX_TMP_FIX=PASS"
echo "V65_98A_LIVE_OBSERVATION=PASS"
echo "V65_98A_PASSIVE_LOOP=PASS"
echo "V65_98A_COMPLETE"
