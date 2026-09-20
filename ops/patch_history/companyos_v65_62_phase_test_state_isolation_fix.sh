#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
export GIT_PAGER=cat
export PAGER=cat

echo "===== COMPANYOS V65.62 PHASE TEST STATE ISOLATION FIX ====="

python - <<'PY'
from pathlib import Path
import ast, shutil, time, py_compile, subprocess, sys

ROOT = Path.home() / "companyos"

# Resolve exact test file dynamically.
TEST = None
TEXT = None
for p in sorted((ROOT / "tests").rglob("*.py")):
    try:
        txt = p.read_text(errors="ignore")
    except Exception:
        continue
    if (
        "def test_internal_work_executes" in txt
        and "def test_external_action_is_held" in txt
        and "phase18601_19000_test" in txt
    ):
        TEST = p
        TEXT = txt
        break

if TEST is None:
    raise SystemExit("V65_62_ABORT=phase_test_file_not_found")

print("TARGET_TEST_FILE=", TEST)

# Show whether stale test state already exists.
STATE_ROOT = ROOT / "companyos_runtime" / "phase18601_19000_test"
print("TEST_STATE_ROOT=", STATE_ROOT)
if STATE_ROOT.exists():
    files = sorted(p for p in STATE_ROOT.rglob("*") if p.is_file())
    print("PREEXISTING_TEST_STATE_FILES=", len(files))
    for p in files[:80]:
        print("STATE_FILE=", p.relative_to(ROOT))
else:
    print("PREEXISTING_TEST_STATE_FILES=0")

# First prove the stale-state hypothesis without changing source/test code.
CLEAN_PROBE = ROOT / "companyos_runtime" / "phase18601_19000_test"
if CLEAN_PROBE.exists():
    shutil.rmtree(CLEAN_PROBE)
    print("TEST_STATE_CLEANED_FOR_PROBE=TRUE")
else:
    print("TEST_STATE_CLEANED_FOR_PROBE=NOT_NEEDED")

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

probe_rc = run(
    "CLEAN_STATE_PHASE_PROBE",
    [sys.executable, "-m", "pytest", "-q", str(TEST)],
    180,
)

if probe_rc != 0:
    print("STALE_STATE_HYPOTHESIS=NOT_CONFIRMED")
    raise SystemExit("V65_62_ABORT=clean_state_phase_test_still_fails")

print("STALE_STATE_HYPOTHESIS=CONFIRMED")

# Permanently isolate this test file by clearing only its test-specific state dir
# each time kernel(name) is constructed. This does NOT touch production runtime state.
BACKUP = TEST.with_name(f"{TEST.name}.v65_62_backup_{int(time.time())}")
shutil.copy2(TEST, BACKUP)
print("BACKUP=", BACKUP)

text = TEST.read_text()
tree = ast.parse(text)

kernel_fn = next(
    (n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "kernel"),
    None,
)
if kernel_fn is None:
    raise SystemExit("V65_62_ABORT=kernel_helper_not_found")

marker = "V65.62 isolate persistent phase test state"

if marker not in text:
    lines = text.splitlines(keepends=True)

    # Ensure shutil import exists.
    if "import shutil" not in text:
        insert_import = 0
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                insert_import = i + 1
        lines.insert(insert_import, "import shutil\n")
        text = "".join(lines)
        tree = ast.parse(text)
        kernel_fn = next(
            n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "kernel"
        )
        lines = text.splitlines(keepends=True)

    # Replace the helper body with deterministic isolated state setup.
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
    print("PATCH_STATUS=test_helper_isolated")
else:
    print("PATCH_STATUS=already_present")

try:
    py_compile.compile(str(TEST), doraise=True)
    print("TEST_FILE_COMPILE=PASS")
except Exception:
    shutil.copy2(BACKUP, TEST)
    print("TEST_FILE_COMPILE=FAIL")
    print("TEST_FILE_RESTORED=TRUE")
    raise

# Run twice back-to-back. The second run is the proof that repeat runs stay clean.
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

# Continue to next full-suite failure.
OUT = Path.home() / ".companyos_runtime/tmp" / f"v65_62_fullsuite_{int(time.time())}.out"
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

print("V65_62_COMPLETE")
PY
