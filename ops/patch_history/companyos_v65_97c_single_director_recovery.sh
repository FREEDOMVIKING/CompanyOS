#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
DL="$HOME/storage/downloads"
GRT="$HOME/.companyos_runtime"
MOD="$ROOT/companyos/runtime/adaptive_capability_director.py"
PIDFILE="$GRT/adaptive_capability_director.pid"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.97C SINGLE DIRECTOR RECOVERY ====="

if [ ! -f "$DL/companyos_v65_97a_capability_test_repair.sh" ]; then
  echo "V65_97C_ABORT=missing_v65_97a_patch"
  exit 1
fi

if [ ! -f "$DL/companyos_v65_97b_integration_scaffold_advancement.sh" ]; then
  echo "V65_97C_ABORT=missing_v65_97b_patch"
  exit 1
fi

echo "===== STOP EVERY ADAPTIVE DIRECTOR PROCESS ====="
pids="$(pgrep -f 'companyos.runtime.adaptive_capability_director' || true)"
if [ -n "${pids:-}" ]; then
  echo "FOUND_DIRECTOR_PIDS=$pids"
  for p in $pids; do
    if [ "$p" != "$$" ]; then
      kill "$p" 2>/dev/null || true
    fi
  done
  sleep 2
  for p in $pids; do
    if [ "$p" != "$$" ] && kill -0 "$p" 2>/dev/null; then
      kill -9 "$p" 2>/dev/null || true
    fi
  done
fi
rm -f "$PIDFILE"

echo "===== REAPPLY TEST-REPAIR LAYER ====="
bash "$DL/companyos_v65_97a_capability_test_repair.sh"

echo "===== REAPPLY SCAFFOLD-ADVANCEMENT LAYER ====="
bash "$DL/companyos_v65_97b_integration_scaffold_advancement.sh"

echo "===== FINAL SOURCE CHECK ====="
grep -n 'def _repair_generation\|def scaffolded_integration_ids\|adaptive_repair_promoted_and_used' "$MOD" || {
  echo "V65_97C_ABORT=required_patch_markers_missing"
  exit 1
}

echo "===== FINAL PROCESS CHECK ====="
sleep 1
count="$(pgrep -f 'python .*companyos.runtime.adaptive_capability_director loop' | wc -l | tr -d ' ')"
echo "DIRECTOR_LOOP_PROCESS_COUNT=$count"

if [ "$count" -ne 1 ]; then
  echo "V65_97C_ABORT=expected_exactly_one_director_loop"
  pgrep -af 'adaptive_capability_director' || true
  exit 1
fi

pid="$(pgrep -f 'python .*companyos.runtime.adaptive_capability_director loop' | head -n1)"
echo "$pid" > "$PIDFILE"
echo "ACTIVE_DIRECTOR_PID=$pid"

echo "===== CURRENT STATUS ====="
python -m companyos.runtime.adaptive_capability_director status || true

echo "===== LATEST LOG ====="
tail -n 80 "$GRT/adaptive_capability_director.log" 2>/dev/null || true

echo "V65_97C_SINGLE_PROCESS=PASS"
echo "V65_97C_REPAIR_LOOP_PRESENT=PASS"
echo "V65_97C_SCAFFOLD_ADVANCEMENT_PRESENT=PASS"
echo "V65_97C_COMPLETE"
