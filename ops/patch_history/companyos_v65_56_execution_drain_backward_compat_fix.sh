#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
export GIT_PAGER=cat
export PAGER=cat

echo "===== COMPANYOS V65.56 EXECUTION DRAIN BACKWARD-COMPAT FIX ====="

python - <<'PY'
from pathlib import Path
import ast, shutil, time, py_compile, subprocess, sys, inspect

ROOT = Path.home() / "companyos"
SRC = ROOT / "companyos/runtime/execution_drain_engine.py"
TEST = ROOT / "tests/test_execution_drain_engine.py"
BACKUP = SRC.with_name(f"execution_drain_engine.py.v65_56_backup_{int(time.time())}")

text = SRC.read_text()
shutil.copy2(SRC, BACKUP)
print("BACKUP=", BACKUP)

tree = ast.parse(text)
klass = next(
    (n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "ExecutionDrainEngine"),
    None,
)
if klass is None:
    raise SystemExit("V65_56_ABORT=class_not_found")

init_fn = next(
    (n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name == "__init__"),
    None,
)
drain_fn = next(
    (n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name == "drain_once"),
    None,
)
if init_fn is None or drain_fn is None:
    raise SystemExit("V65_56_ABORT=required_method_not_found")

lines = text.splitlines(keepends=True)

new_init = [
    "    def __init__(self, queue: AutonomousTaskQueue | int, dispatcher: Any = None, batch_size: int = 32):\n",
    "        # V65.56 compatibility: historical callers may construct with only\n",
    "        # an integer to inspect the bounded batch size. That path is config-only\n",
    "        # and cannot dispatch work. Live execution still requires a dispatcher.\n",
    "        if dispatcher is None and isinstance(queue, int):\n",
    "            self.queue = None\n",
    "            self.dispatcher = None\n",
    "            self.batch_size = max(1, min(int(queue), 128))\n",
    "            self._config_only = True\n",
    "            return\n",
    "        if dispatcher is None or not hasattr(dispatcher, \"dispatch_next\"):\n",
    "            raise TypeError(\"live_dependency_dispatcher_required\")\n",
    "        self.queue = queue\n",
    "        self.dispatcher = dispatcher\n",
    "        self.batch_size = max(1, min(int(batch_size), 128))\n",
    "        self._config_only = False\n",
]

# Replace __init__ bottom-up so AST line numbers remain valid for drain patch.
start = init_fn.lineno - 1
end = init_fn.end_lineno
lines[start:end] = new_init
patched = "".join(lines)

# Reparse and add explicit live guard at top of drain_once.
tree2 = ast.parse(patched)
klass2 = next(n for n in tree2.body if isinstance(n, ast.ClassDef) and n.name == "ExecutionDrainEngine")
drain2 = next(n for n in klass2.body if isinstance(n, ast.FunctionDef) and n.name == "drain_once")
lines2 = patched.splitlines(keepends=True)

guard = [
    "        if self.dispatcher is None:\n",
    "            raise RuntimeError(\"live_dependency_dispatcher_required\")\n",
]
insert_at = drain2.body[0].lineno - 1
if "if self.dispatcher is None:" not in patched:
    lines2[insert_at:insert_at] = guard

SRC.write_text("".join(lines2))
print("PATCH=compat_constructor_plus_live_guard")

try:
    py_compile.compile(str(SRC), doraise=True)
    print("PY_COMPILE=PASS")
except Exception:
    shutil.copy2(BACKUP, SRC)
    print("PY_COMPILE=FAIL")
    print("SOURCE_RESTORED=TRUE")
    raise

# Runtime contract probe.
import importlib
mod = importlib.import_module("companyos.runtime.execution_drain_engine")
mod = importlib.reload(mod)
Engine = mod.ExecutionDrainEngine

print("ENGINE_SIGNATURE=", inspect.signature(Engine))
print("BATCH_0=", Engine(0).batch_size)
print("BATCH_999=", Engine(999).batch_size)

if Engine(0).batch_size != 1:
    shutil.copy2(BACKUP, SRC)
    raise SystemExit("V65_56_ABORT=batch_lower_bound_wrong")
if Engine(999).batch_size != 128:
    shutil.copy2(BACKUP, SRC)
    raise SystemExit("V65_56_ABORT=batch_upper_bound_wrong")

try:
    Engine(4).drain_once()
except RuntimeError as exc:
    print("CONFIG_ONLY_DRAIN_GUARD=", str(exc))
    if str(exc) != "live_dependency_dispatcher_required":
        shutil.copy2(BACKUP, SRC)
        raise
else:
    shutil.copy2(BACKUP, SRC)
    raise SystemExit("V65_56_ABORT=config_only_drain_not_blocked")

class DummyDispatcher:
    def dispatch_next(self):
        class R:
            dispatched = False
            reason = "dummy_stop"
        return R()

live = Engine(queue=object(), dispatcher=DummyDispatcher(), batch_size=999)
print("LIVE_BATCH_999=", live.batch_size)
if live.batch_size != 128:
    shutil.copy2(BACKUP, SRC)
    raise SystemExit("V65_56_ABORT=live_batch_upper_bound_wrong")

result = live.drain_once()
print("LIVE_DRAIN_REASON=", result.stopped_reason)
if result.stopped_reason != "dummy_stop":
    shutil.copy2(BACKUP, SRC)
    raise SystemExit("V65_56_ABORT=live_dispatch_path_broken")

def run(label, args, timeout=180):
    cp = subprocess.run(args, cwd=str(ROOT), text=True, capture_output=True, timeout=timeout)
    print(f"\n===== {label} =====")
    print("RETURN_CODE=", cp.returncode)
    if cp.stdout:
        print(cp.stdout[-16000:])
    if cp.stderr:
        print(cp.stderr[-6000:])
    return cp.returncode

rc = run(
    "TARGET_TEST",
    [sys.executable, "-m", "pytest", "-q", str(TEST)],
    90,
)
if rc != 0:
    shutil.copy2(BACKUP, SRC)
    py_compile.compile(str(SRC), doraise=True)
    print("TARGET_TEST=FAIL")
    print("SOURCE_RESTORED=TRUE")
    raise SystemExit(rc)

print("TARGET_TEST=PASS")

# Scan to the next full-suite failure immediately.
OUT = Path.home() / ".companyos_runtime/tmp" / f"v65_56_fullsuite_{int(time.time())}.out"
OUT.parent.mkdir(parents=True, exist_ok=True)

with OUT.open("w") as fh:
    cp = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-x"],
        cwd=str(ROOT),
        text=True,
        stdout=fh,
        stderr=subprocess.STDOUT,
        timeout=900,
    )

print("FULL_SUITE_RETURN_CODE=", cp.returncode)
tail = OUT.read_text(errors="ignore").splitlines()[-180:]
print("FULL_SUITE_TAIL_BEGIN")
print("\n".join(tail))
print("FULL_SUITE_TAIL_END")
print("FULL_SUITE_OUTPUT=", OUT)

if cp.returncode == 0:
    print("FULL_SUITE=PASS")
else:
    print("FULL_SUITE=NEXT_FAILURE_FOUND")

print("SOURCE_RESTORED=FALSE")
print("V65_56_COMPLETE")
PY
