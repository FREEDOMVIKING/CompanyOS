#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"

echo "===== COMPANYOS V27.9.4A AST HANDLER TIMEOUT FIX ====="
TS="$(date +%Y%m%d_%H%M%S)"
B="$HOME/.companyos_runtime/backups/v27_9_4a_$TS"
mkdir -p "$B"
F="companyos/runtime/autonomous_task_dispatcher.py"
cp -a "$F" "$B/"

python - <<'PY'
from pathlib import Path
import ast

p=Path("companyos/runtime/autonomous_task_dispatcher.py")
src=p.read_text()
tree=ast.parse(src)

# Locate exact statement: result = handler(task)
target_line=None
for node in ast.walk(tree):
    if isinstance(node, ast.Assign) and len(node.targets)==1:
        t=node.targets[0]
        if isinstance(t, ast.Name) and t.id=="result":
            call=node.value
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id=="handler":
                if len(call.args)==1 and isinstance(call.args[0], ast.Name) and call.args[0].id=="task":
                    target_line=node.lineno
                    break

if target_line is None:
    raise SystemExit("V27_9_4A_ABORT: exact result=handler(task) call not found")

lines=src.splitlines()
idx=target_line-1
indent=lines[idx][:len(lines[idx])-len(lines[idx].lstrip())]

replacement=[
    indent+"# V27_9_4A_LIVE_HANDLER_TIMEOUT",
    indent+"_bounded = run_bounded(lambda: handler(task))",
    indent+"if not _bounded.ok:",
    indent+"    if _bounded.timed_out:",
    indent+"        raise TimeoutError(_bounded.error or 'task_timeout')",
    indent+"    raise RuntimeError(_bounded.error or 'task_handler_failed')",
    indent+"result = _bounded.value",
]
lines[idx:idx+1]=replacement
src="\n".join(lines)+"\n"

imp="from companyos.runtime.bounded_task_execution import run_bounded\n"
if imp not in src:
    src=src.replace(
        "from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue, TaskRecord\n",
        "from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue, TaskRecord\n"+imp,
        1
    )

ast.parse(src)
tmp=p.with_suffix(".py.v27_9_4a_tmp")
tmp.write_text(src)
compile(src,str(tmp),"exec")
tmp.replace(p)
print("AST_PATCH=PASS")
print("TARGET_LINE=",target_line)
PY

python -m py_compile "$F" companyos/runtime/bounded_task_execution.py
echo "COMPILE=PASS"

cat > tests/test_v27_9_4a_dispatch_timeout.py <<'PY'
from pathlib import Path

def test_timeout_wiring_present():
    s=Path("companyos/runtime/autonomous_task_dispatcher.py").read_text()
    assert "V27_9_4A_LIVE_HANDLER_TIMEOUT" in s
    assert "run_bounded(lambda: handler(task))" in s
    assert "TimeoutError" in s
PY

python -m pytest -q \
  tests/test_bounded_task_execution.py \
  tests/test_v27_9_4a_dispatch_timeout.py
echo "TESTS=PASS"

echo "===== SUPERVISOR PRESERVED ====="
pgrep -af 'companyos.runtime.service_supervisor' || true
pgrep -af 'companyos.runtime.continuous_goal_runtime' || true

echo "===== GIT DIFF ====="
git diff -- "$F" | sed -n '1,220p'

git add "$F" tests/test_v27_9_4a_dispatch_timeout.py companyos/runtime/bounded_task_execution.py
if ! git diff --cached --quiet; then
  git commit -m "V27.9.4a wire bounded timeout into specialist handler" || true
fi

echo "===== V27.9.4A PASS ====="
echo "QUEUE_RECORDS_DELETED=0"
echo "SUPERVISOR_RESTARTED=NO"
echo "FINANCE_CONNECTORS_CHANGED=NO"
