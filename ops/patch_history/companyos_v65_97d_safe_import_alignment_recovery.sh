#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
GRT="$HOME/.companyos_runtime"
ACD="$ROOT/companyos/runtime/adaptive_capability_director.py"
CAP="$ROOT/companyos/runtime/capability_expansion.py"
PIDFILE="$GRT/adaptive_capability_director.pid"
LOGFILE="$GRT/adaptive_capability_director.log"
INTERVAL="${COMPANYOS_CAPABILITY_DIRECTOR_INTERVAL_SECONDS:-900}"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.97D SAFE IMPORT ALIGNMENT + RECOVERY ====="

# Make sure no stale director loop survives.
pids="$(pgrep -f 'companyos.runtime.adaptive_capability_director loop' || true)"
if [ -n "${pids:-}" ]; then
  echo "STOPPING_DIRECTOR_PIDS=$pids"
  for p in $pids; do
    [ "$p" = "$$" ] || kill "$p" 2>/dev/null || true
  done
  sleep 2
  for p in $pids; do
    if [ "$p" != "$$" ] && kill -0 "$p" 2>/dev/null; then
      kill -9 "$p" 2>/dev/null || true
    fi
  done
fi
rm -f "$PIDFILE"

[ -f "$ACD" ] || { echo "V65_97D_ABORT=adaptive_director_missing"; exit 1; }
[ -f "$CAP" ] || { echo "V65_97D_ABORT=capability_expansion_missing"; exit 1; }

stamp="$(date +%Y%m%d_%H%M%S)"
cp "$ACD" "${ACD}.v65_97d_backup_${stamp}"
cp "$CAP" "${CAP}.v65_97d_backup_${stamp}"
echo "BACKUP_DIRECTOR=${ACD}.v65_97d_backup_${stamp}"
echo "BACKUP_EXPANSION=${CAP}.v65_97d_backup_${stamp}"

python - <<'PY'
from pathlib import Path

root = Path.home() / "companyos"
acd = root / "companyos/runtime/adaptive_capability_director.py"
cap = root / "companyos/runtime/capability_expansion.py"

a = acd.read_text(encoding="utf-8")
c = cap.read_text(encoding="utf-8")

# 97A/97B are already present if these markers exist. Do not destructively
# reapply an older patch over already-upgraded source.
repair_ok = "def _repair_generation(" in a and "adaptive_repair_promoted_and_used" in a
scaffold_ok = "def scaffolded_integration_ids(" in a

print("REPAIR_LOOP_PRESENT=", repair_ok)
print("SCAFFOLD_ADVANCEMENT_PRESENT=", scaffold_ok)

if not repair_ok:
    raise SystemExit("V65_97D_ABORT=97A_repair_loop_missing")
if not scaffold_ok:
    raise SystemExit("V65_97D_ABORT=97B_scaffold_advancement_missing")

# The failed app_problem_ranker candidate used Python's harmless stdlib `copy`
# module. Align the validator with that safe analytical use instead of weakening
# import validation broadly.
old = 'SAFE_IMPORTS={"json","re","math","statistics","time","pathlib","typing","dataclasses","collections","itertools","functools","unittest"}'
new = 'SAFE_IMPORTS={"json","re","math","statistics","time","pathlib","typing","dataclasses","collections","itertools","functools","unittest","copy"}'

if old in c:
    c = c.replace(old, new)
    print("SAFE_IMPORT_COPY_ADDED=PASS")
elif '"copy"' in c.split("SAFE_IMPORTS=",1)[1].split("\n",1)[0]:
    print("SAFE_IMPORT_COPY_ALREADY_PRESENT=true")
else:
    raise SystemExit("V65_97D_ABORT=safe_imports_signature_not_found")

# Make the generation prompt explicit so retries stop inventing disallowed
# dependencies. This keeps the allowlist narrow and deterministic.
needle = "- Pure analysis only.\n"
extra = '- Allowed imports only: json, re, math, statistics, time, pathlib, typing, dataclasses, collections, itertools, functools, copy, unittest.\\n'
if needle in c and "Allowed imports only:" not in c:
    c = c.replace(needle, needle + extra, 1)
    print("GENERATOR_ALLOWED_IMPORT_HINT=PASS")
else:
    print("GENERATOR_ALLOWED_IMPORT_HINT=UNCHANGED")

cap.write_text(c, encoding="utf-8")
PY

python -m py_compile "$ACD" "$CAP"
echo "MODULE_COMPILE=PASS"

echo "===== RETRY CAPABILITY EXPANSION ====="
python -m companyos.runtime.adaptive_capability_director once

echo "===== RESTART SINGLE BACKGROUND DIRECTOR ====="
nohup python -m companyos.runtime.adaptive_capability_director loop \
  --interval "$INTERVAL" >>"$LOGFILE" 2>&1 &
pid="$!"
echo "$pid" >"$PIDFILE"
sleep 1

if ! kill -0 "$pid" 2>/dev/null; then
  rm -f "$PIDFILE"
  echo "V65_97D_ABORT=director_failed_to_start"
  exit 1
fi

count="$(pgrep -f 'python .*companyos.runtime.adaptive_capability_director loop' | wc -l | tr -d ' ')"
echo "DIRECTOR_LOOP_PROCESS_COUNT=$count"
echo "ACTIVE_DIRECTOR_PID=$pid"

if [ "$count" -ne 1 ]; then
  echo "V65_97D_ABORT=expected_exactly_one_director_loop"
  pgrep -af 'adaptive_capability_director' || true
  exit 1
fi

echo "===== FINAL PATCH CHECK ====="
grep -n 'def _repair_generation\|def scaffolded_integration_ids\|SAFE_IMPORTS=' "$ACD" "$CAP" || true

echo "V65_97D_SAFE_IMPORT_ALIGNMENT=PASS"
echo "V65_97D_REPAIR_LOOP_PRESENT=PASS"
echo "V65_97D_SCAFFOLD_ADVANCEMENT_PRESENT=PASS"
echo "V65_97D_SINGLE_DIRECTOR=PASS"
echo "V65_97D_COMPLETE"
