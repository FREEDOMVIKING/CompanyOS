#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
echo "===== COMPANYOS V27.9.4 LIVE HANDLER TIMEOUT WIRING ====="
TS="$(date +%Y%m%d_%H%M%S)"
B="$HOME/.companyos_runtime/backups/v27_9_4_$TS"
mkdir -p "$B"
F="companyos/runtime/autonomous_task_dispatcher.py"
[ -f "$F" ] || { echo "ABORT: $F missing"; exit 1; }
cp -a "$F" "$B/"

python - <<'PY'
from pathlib import Path
import ast,re
p=Path("companyos/runtime/autonomous_task_dispatcher.py")
s=p.read_text()
ast.parse(s)
print("SOURCE_PARSE_PASS")
# Inventory likely handler invocation sites without changing them yet.
for i,l in enumerate(s.splitlines(),1):
    if any(x in l for x in ("handlers[", ".handlers.get(", "handler(")):
        print(f"CALLSITE {i}: {l[:180]}")
PY

python - <<'PY'
from pathlib import Path
import re,ast
p=Path("companyos/runtime/autonomous_task_dispatcher.py")
s=p.read_text()
if "V27_9_4_LIVE_HANDLER_TIMEOUT" in s:
    print("ALREADY_WIRED")
    raise SystemExit

# Import bounded executor.
imp="from companyos.runtime.bounded_task_execution import run_bounded\n"
if imp not in s:
    lines=s.splitlines(True)
    idx=0
    while idx<len(lines) and (lines[idx].startswith("from __future__") or lines[idx].strip()==""):
        idx+=1
    lines.insert(idx,imp)
    s="".join(lines)

# Patch only a simple direct assignment invocation of a variable named handler.
patterns=[
    (r'(?m)^(\s*)(result\s*=\s*)handler\(([^\\n]*)\)\s*$',
     r'\1# V27_9_4_LIVE_HANDLER_TIMEOUT\n\1_bounded = run_bounded(lambda: handler(\3))\n\1if not _bounded.ok:\n\1    raise TimeoutError(_bounded.error) if _bounded.timed_out else RuntimeError(_bounded.error)\n\1result = _bounded.value'),
    (r'(?m)^(\s*)(return\s+)handler\(([^\\n]*)\)\s*$',
     r'\1# V27_9_4_LIVE_HANDLER_TIMEOUT\n\1_bounded = run_bounded(lambda: handler(\3))\n\1if not _bounded.ok:\n\1    raise TimeoutError(_bounded.error) if _bounded.timed_out else RuntimeError(_bounded.error)\n\1return _bounded.value'),
]
n=0
for pat,repl in patterns:
    s2,c=re.subn(pat,repl,s,count=1)
    if c:
        s=s2;n+=c;break

if not n:
    print("ABORT_NO_SAFE_DIRECT_HANDLER_CALL_FOUND")
    raise SystemExit(42)

ast.parse(s)
p.write_text(s)
print("LIVE_HANDLER_WIRED=1")
PY
rc=$?
if [ "$rc" -eq 42 ]; then
  echo "No source mutation made beyond in-memory attempt; restoring."
  cp "$B/autonomous_task_dispatcher.py" "$F"
  exit 42
elif [ "$rc" -ne 0 ]; then
  cp "$B/autonomous_task_dispatcher.py" "$F"
  exit "$rc"
fi

python -m py_compile "$F" companyos/runtime/bounded_task_execution.py

cat > tests/test_v27_9_4_timeout_wiring.py <<'PY'
from pathlib import Path
def test_wiring_present():
    s=Path("companyos/runtime/autonomous_task_dispatcher.py").read_text()
    assert "V27_9_4_LIVE_HANDLER_TIMEOUT" in s
    assert "run_bounded" in s
PY
python -m pytest -q tests/test_bounded_task_execution.py tests/test_v27_9_4_timeout_wiring.py

echo "===== PRESERVE LIVE PROCESSES ====="
pgrep -af 'companyos.runtime.service_supervisor' || true
pgrep -af 'companyos.runtime.continuous_goal_runtime' || true

git add "$F" companyos/runtime/bounded_task_execution.py tests/test_v27_9_4_timeout_wiring.py
if ! git diff --cached --quiet; then
  git commit -m "V27.9.4 wire bounded timeout into live task handler" || true
fi

echo "===== V27.9.4 PASS ====="
echo "TIMEOUT_SECONDS=${COMPANYOS_TASK_TIMEOUT_SECONDS:-90}"
echo "QUEUE_RECORDS_DELETED=0"
echo "SUPERVISOR_RESTART=NO"
echo "FINANCE_CONNECTORS_CHANGED=NO"
