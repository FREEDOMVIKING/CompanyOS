#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
export GIT_PAGER=cat
export PAGER=cat

echo "===== COMPANYOS V65.61 ENQUEUE SINGLETON COMPAT FIX ====="

python - <<'PY'
from pathlib import Path
import ast, shutil, time, py_compile, subprocess, sys, importlib, inspect, tempfile

ROOT = Path.home() / "companyos"
SRC = ROOT / "companyos/modules/phase18601_19000/autonomous_operations_kernel.py"
TEST = ROOT / "tests/test_phase18601_19000.py"
BACKUP = SRC.with_name(f"autonomous_operations_kernel.py.v65_61_backup_{int(time.time())}")

text = SRC.read_text()
shutil.copy2(SRC, BACKUP)
print("BACKUP=", BACKUP)

tree = ast.parse(text)
klass = next(
    (n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "AutonomousOperationsKernel"),
    None,
)
if klass is None:
    raise SystemExit("V65_61_ABORT=kernel_class_not_found")

enqueue_fn = next(
    (n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name == "enqueue"),
    None,
)
if enqueue_fn is None:
    raise SystemExit("V65_61_ABORT=enqueue_not_found")

lines = text.splitlines(keepends=True)
marker = "V65.61 backward compatibility: accept one WorkItem or an iterable"

if marker not in text:
    # Insert immediately after def line, before queue loading.
    insert_at = enqueue_fn.lineno
    indent = "        "
    block = [
        indent + "# " + marker + "\n",
        indent + "if isinstance(items, WorkItem):\n",
        indent + "    items = [items]\n",
        indent + "else:\n",
        indent + "    items = list(items)\n",
    ]
    lines[insert_at:insert_at] = block
    SRC.write_text("".join(lines))
    print("PATCH_STATUS=inserted")
else:
    print("PATCH_STATUS=already_present")

try:
    py_compile.compile(str(SRC), doraise=True)
    print("PY_COMPILE=PASS")
except Exception:
    shutil.copy2(BACKUP, SRC)
    print("PY_COMPILE=FAIL")
    print("SOURCE_RESTORED=TRUE")
    raise

# Reload exact module and prove both singleton and list contracts in isolated state.
mod = importlib.import_module("companyos.modules.phase18601_19000.autonomous_operations_kernel")
mod = importlib.reload(mod)
Kernel = mod.AutonomousOperationsKernel
WorkItem = mod.WorkItem

print("ENQUEUE_SIGNATURE=", inspect.signature(Kernel.enqueue))

with tempfile.TemporaryDirectory() as td:
    k = Kernel(state_dir=Path(td))

    a = WorkItem("a", "alpha", "Research", 90, 0.8, 0.2, [], ["research"])
    r1 = k.enqueue(a)
    print("SINGLETON_ENQUEUE_RESULT=", r1)

    b = WorkItem("b", "beta", "Research", 80, 0.7, 0.2, [], ["research"])
    r2 = k.enqueue([b])
    print("LIST_ENQUEUE_RESULT=", r2)

    q = k.load_queue()
    print("QUEUE_IDS=", [x.work_id for x in q])

    if {x.work_id for x in q} != {"a", "b"}:
        shutil.copy2(BACKUP, SRC)
        raise SystemExit("V65_61_ABORT=enqueue_contract_probe_failed")

print("ENQUEUE_COMPAT_PROOF=PASS")

def run(label, args, timeout=180):
    cp = subprocess.run(
        args,
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    print(f"\n===== {label} =====")
    print("RETURN_CODE=", cp.returncode)
    if cp.stdout:
        print(cp.stdout[-16000:])
    if cp.stderr:
        print(cp.stderr[-6000:])
    return cp.returncode

# Run exact phase file to verify internal work execution path.
rc = run(
    "PHASE18601_19000_TEST_FILE",
    [sys.executable, "-m", "pytest", "-q", str(TEST)],
    180,
)
if rc != 0:
    shutil.copy2(BACKUP, SRC)
    py_compile.compile(str(SRC), doraise=True)
    print("PHASE_TEST=FAIL")
    print("SOURCE_RESTORED=TRUE")
    raise SystemExit(rc)

print("PHASE_TEST=PASS")

# Continue immediately to next full-suite failure.
OUT = Path.home() / ".companyos_runtime/tmp" / f"v65_61_fullsuite_{int(time.time())}.out"
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
print("V65_61_COMPLETE")
PY
