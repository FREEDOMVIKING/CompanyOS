#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
export GIT_PAGER=cat
export PAGER=cat

echo "===== COMPANYOS V65.65 LIVE HANDLER TIMEOUT WIRING FIX ====="

python - <<'PY'
from pathlib import Path
import shutil, time, py_compile, subprocess, sys, ast

ROOT = Path.home() / "companyos"
SRC = ROOT / "companyos/runtime/autonomous_task_dispatcher.py"
TEST = ROOT / "tests/test_v27_9_4a_dispatch_timeout.py"

if not SRC.exists():
    raise SystemExit("V65_65_ABORT=dispatcher_source_missing")
if not TEST.exists():
    raise SystemExit("V65_65_ABORT=timeout_test_missing")

BACKUP = SRC.with_name(f"{SRC.name}.v65_65_backup_{int(time.time())}")
shutil.copy2(SRC, BACKUP)
print("BACKUP=", BACKUP)

text = SRC.read_text()

# Add bounded execution import if missing.
if "from companyos.runtime.bounded_task_execution import run_bounded" not in text:
    anchor = "from companyos.runtime.lease_execution_guard import LeaseExecutionGuard\n"
    if anchor not in text:
        shutil.copy2(BACKUP, SRC)
        raise SystemExit("V65_65_ABORT=import_anchor_not_found")
    text = text.replace(
        anchor,
        anchor + "from companyos.runtime.bounded_task_execution import run_bounded\n",
        1,
    )

marker = "V27_9_4A_LIVE_HANDLER_TIMEOUT"

old = '''            ok, result, error = guard.execute(
                task_id,
                owner,
                lambda: handler(task),
            )
'''

new = '''            # V27_9_4A_LIVE_HANDLER_TIMEOUT
            # Keep the lease/fencing guard authoritative while bounding the
            # handler itself so a stuck agent cannot hold the dispatcher forever.
            def _bounded_handler():
                bounded = run_bounded(lambda: handler(task))
                if bounded.timed_out:
                    raise TimeoutError(bounded.error or "live_handler_timeout")
                if not bounded.ok:
                    raise RuntimeError(bounded.error or "bounded_handler_failed")
                return bounded.value

            ok, result, error = guard.execute(
                task_id,
                owner,
                _bounded_handler,
            )
'''

if marker not in text:
    if old not in text:
        shutil.copy2(BACKUP, SRC)
        raise SystemExit("V65_65_ABORT=dispatch_guard_anchor_not_found")
    text = text.replace(old, new, 1)
    print("PATCH_STATUS=inserted")
else:
    print("PATCH_STATUS=already_present")

SRC.write_text(text)

try:
    ast.parse(SRC.read_text())
    py_compile.compile(str(SRC), doraise=True)
    print("DISPATCHER_COMPILE=PASS")
except Exception:
    shutil.copy2(BACKUP, SRC)
    print("DISPATCHER_COMPILE=FAIL")
    print("SOURCE_RESTORED=TRUE")
    raise

patched = SRC.read_text()
required = [
    "V27_9_4A_LIVE_HANDLER_TIMEOUT",
    "run_bounded(lambda: handler(task))",
    "TimeoutError",
]
missing = [x for x in required if x not in patched]
print("TIMEOUT_CONTRACT_MISSING=", missing)
if missing:
    shutil.copy2(BACKUP, SRC)
    raise SystemExit("V65_65_ABORT=timeout_contract_missing")

print("TIMEOUT_CONTRACT_PROOF=PASS")

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

rc = run(
    "TARGET_TIMEOUT_TEST",
    [sys.executable, "-m", "pytest", "-q", str(TEST)],
    120,
)
if rc != 0:
    shutil.copy2(BACKUP, SRC)
    py_compile.compile(str(SRC), doraise=True)
    print("TARGET_TEST=FAIL")
    print("SOURCE_RESTORED=TRUE")
    raise SystemExit(rc)

print("TARGET_TEST=PASS")

dispatcher_tests = sorted(
    str(p.relative_to(ROOT))
    for p in (ROOT / "tests").glob("*dispatch*.py")
    if p.is_file()
)
if dispatcher_tests:
    rc = run(
        "DISPATCHER_TESTS",
        [sys.executable, "-m", "pytest", "-q", *dispatcher_tests],
        300,
    )
    if rc != 0:
        shutil.copy2(BACKUP, SRC)
        py_compile.compile(str(SRC), doraise=True)
        print("DISPATCHER_TESTS=FAIL")
        print("SOURCE_RESTORED=TRUE")
        raise SystemExit(rc)
    print("DISPATCHER_TESTS=PASS")
else:
    print("DISPATCHER_TESTS=NONE_FOUND")

OUT = Path.home() / ".companyos_runtime/tmp" / f"v65_65_fullsuite_{int(time.time())}.out"
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
tail = OUT.read_text(errors="ignore").splitlines()[-220:]
print("FULL_SUITE_TAIL_BEGIN")
print("\n".join(tail))
print("FULL_SUITE_TAIL_END")
print("FULL_SUITE_OUTPUT=", OUT)

if cp.returncode == 0:
    print("FULL_SUITE=PASS")
    print("V65_65_READY_FOR_CHECKPOINT=TRUE")
else:
    print("FULL_SUITE=NEXT_FAILURE_FOUND")
    print("V65_65_READY_FOR_CHECKPOINT=TIMEOUT_ONLY")

print("SOURCE_RESTORED=FALSE")
print("V65_65_COMPLETE")
PY
