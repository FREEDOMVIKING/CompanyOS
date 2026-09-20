#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
export GIT_PAGER=cat
export PAGER=cat

echo "===== COMPANYOS V65.62A TEST STATE ISOLATION RECOVERY ====="

python - <<'PY'
from pathlib import Path
import ast, shutil, time, py_compile, subprocess, sys

ROOT = Path.home() / "companyos"
TEST = ROOT / "tests/test_phase18601_19000.py"

if not TEST.exists():
    raise SystemExit("V65_62A_ABORT=test_file_missing")

print("TARGET_TEST_FILE=", TEST)

# Recover automatically if V65.62 left the test file syntactically broken.
def compiles(path: Path) -> bool:
    try:
        py_compile.compile(str(path), doraise=True)
        return True
    except Exception as exc:
        print("COMPILE_ERROR=", repr(exc))
        return False

if not compiles(TEST):
    backups = sorted(TEST.parent.glob(TEST.name + ".v65_62_backup_*"), key=lambda p: p.stat().st_mtime)
    if not backups:
        raise SystemExit("V65_62A_ABORT=broken_test_and_no_v65_62_backup")
    restore = backups[-1]
    shutil.copy2(restore, TEST)
    print("RECOVERED_FROM=", restore)
    if not compiles(TEST):
        raise SystemExit("V65_62A_ABORT=backup_did_not_compile")
    print("RECOVERY_COMPILE=PASS")
else:
    print("BASELINE_COMPILE=PASS")

# Back up the recovered/healthy baseline before applying V65.62A.
BACKUP = TEST.with_name(f"{TEST.name}.v65_62a_backup_{int(time.time())}")
shutil.copy2(TEST, BACKUP)
print("BACKUP=", BACKUP)

text = TEST.read_text()
tree = ast.parse(text)

kernel_fn = next(
    (n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "kernel"),
    None,
)
if kernel_fn is None:
    raise SystemExit("V65_62A_ABORT=kernel_helper_not_found")

marker = "V65.62A isolate persistent phase test state"

if marker not in text:
    # Add shutil safely right after the simple `import sys` line.
    if "import shutil\n" not in text:
        if "import sys\n" not in text:
            raise SystemExit("V65_62A_ABORT=import_sys_anchor_not_found")
        text = text.replace("import sys\n", "import sys\nimport shutil\n", 1)

    # Reparse after import insertion so line numbers are correct.
    tree = ast.parse(text)
    kernel_fn = next(
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "kernel"
    )

    lines = text.splitlines(keepends=True)
    start = kernel_fn.body[0].lineno - 1
    end = kernel_fn.end_lineno

    indent = "    "
    body = [
        indent + "# " + marker + "\n",
        indent + 'state_dir = ROOT / "companyos_runtime" / "phase18601_19000_test" / name\n',
        indent + "if state_dir.exists():\n",
        indent + "    shutil.rmtree(state_dir)\n",
        indent + "return AutonomousOperationsKernel(state_dir)\n",
    ]

    lines[start:end] = body
    TEST.write_text("".join(lines))
    print("PATCH_STATUS=applied")
else:
    print("PATCH_STATUS=already_present")

# Hard compile gate with automatic rollback.
try:
    py_compile.compile(str(TEST), doraise=True)
    print("TEST_FILE_COMPILE=PASS")
except Exception:
    shutil.copy2(BACKUP, TEST)
    print("TEST_FILE_COMPILE=FAIL")
    print("TEST_FILE_RESTORED=TRUE")
    raise

# Show the patched helper.
patched = TEST.read_text()
ptree = ast.parse(patched)
pfn = next(n for n in ptree.body if isinstance(n, ast.FunctionDef) and n.name == "kernel")
pls = patched.splitlines()
print("PATCHED_KERNEL_HELPER_BEGIN")
for i in range(pfn.lineno, pfn.end_lineno + 1):
    print(f"{i:04d}: {pls[i-1]}")
print("PATCHED_KERNEL_HELPER_END")

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
        print(cp.stdout[-18000:])
    if cp.stderr:
        print(cp.stderr[-6000:])
    return cp.returncode

# Prove repeatability. These runs should both pass even back-to-back.
rc1 = run(
    "PHASE_TEST_REPEAT_1",
    [sys.executable, "-m", "pytest", "-q", str(TEST)],
    180,
)
rc2 = run(
    "PHASE_TEST_REPEAT_2",
    [sys.executable, "-m", "pytest", "-q", str(TEST)],
    180,
)

if rc1 != 0 or rc2 != 0:
    shutil.copy2(BACKUP, TEST)
    py_compile.compile(str(TEST), doraise=True)
    print("REPEATABILITY_PROOF=FAIL")
    print("TEST_FILE_RESTORED=TRUE")
    raise SystemExit(1)

print("REPEATABILITY_PROOF=PASS")
print("PHASE_TEST=PASS")

# Continue into the full suite and stop on the next real failure.
OUT = Path.home() / ".companyos_runtime/tmp" / f"v65_62a_fullsuite_{int(time.time())}.out"
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
tail = OUT.read_text(errors="ignore").splitlines()[-200:]
print("FULL_SUITE_TAIL_BEGIN")
print("\n".join(tail))
print("FULL_SUITE_TAIL_END")
print("FULL_SUITE_OUTPUT=", OUT)

if cp.returncode == 0:
    print("FULL_SUITE=PASS")
    print("V65_62A_READY_FOR_CHECKPOINT=TRUE")
else:
    print("FULL_SUITE=NEXT_FAILURE_FOUND")
    print("V65_62A_READY_FOR_CHECKPOINT=PHASE_ONLY")

print("V65_62A_COMPLETE")
PY
