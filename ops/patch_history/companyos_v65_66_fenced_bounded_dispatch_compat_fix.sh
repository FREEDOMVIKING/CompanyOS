#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
export GIT_PAGER=cat
export PAGER=cat

echo "===== COMPANYOS V65.66 FENCED + BOUNDED DISPATCH COMPAT FIX ====="

python - <<'PY'
from pathlib import Path
import shutil, time, py_compile, subprocess, sys, ast, re

ROOT = Path.home() / "companyos"
SRC = ROOT / "companyos/runtime/autonomous_task_dispatcher.py"
T27 = ROOT / "tests/test_v27_9_4a_dispatch_timeout.py"
T35 = ROOT / "tests/test_v35_1_dispatcher_ast_contract.py"

for p, label in [(SRC, "dispatcher_source"), (T27, "v27_test"), (T35, "v35_test")]:
    if not p.exists():
        raise SystemExit(f"V65_66_ABORT={label}_missing:{p}")

BACKUP = SRC.with_name(f"{SRC.name}.v65_66_backup_{int(time.time())}")
shutil.copy2(SRC, BACKUP)
print("BACKUP=", BACKUP)

text = SRC.read_text()

# Ensure bounded execution import.
bounded_import = "from companyos.runtime.bounded_task_execution import run_bounded\n"
lease_import = "from companyos.runtime.lease_execution_guard import LeaseExecutionGuard\n"
if bounded_import not in text:
    if lease_import not in text:
        raise SystemExit("V65_66_ABORT=lease_import_anchor_missing")
    text = text.replace(lease_import, lease_import + bounded_import, 1)

# Replace the current lease execution block, whether baseline or V65.65-shaped.
start_token = "            guard = LeaseExecutionGuard(self.queue.kernel.db_path)\n"
alt_start_token = "            _v35_guard = LeaseExecutionGuard(self.queue.kernel.db_path)\n"

start = text.find(start_token)
if start < 0:
    start = text.find(alt_start_token)

if start < 0:
    shutil.copy2(BACKUP, SRC)
    raise SystemExit("V65_66_ABORT=lease_block_start_not_found")

end_token = "            if not ok:\n"
end = text.find(end_token, start)
if end < 0:
    shutil.copy2(BACKUP, SRC)
    raise SystemExit("V65_66_ABORT=lease_block_end_not_found")

replacement = '''            # V35_1_FENCED_HANDLER_CALL
            # V27_9_4A_LIVE_HANDLER_TIMEOUT
            _v35_guard = LeaseExecutionGuard(self.queue.kernel.db_path)
            task_id = str(task.task_id)
            owner = "dispatcher-" + str(id(self))

            def _bounded_handler():
                bounded = run_bounded(lambda: handler(task))
                if bounded.timed_out:
                    raise TimeoutError(bounded.error or "live_handler_timeout")
                if not bounded.ok:
                    raise RuntimeError(bounded.error or "bounded_handler_failed")
                return bounded.value

            ok, result, error = _v35_guard.execute(
                task_id,
                owner,
                _bounded_handler,
            )
'''

text = text[:start] + replacement + text[end:]
SRC.write_text(text)
print("PATCH_STATUS=normalized_fenced_bounded_dispatch")

# Syntax/compile gate.
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

required_contracts = {
    "V27_TIMEOUT_MARKER": "V27_9_4A_LIVE_HANDLER_TIMEOUT",
    "V27_RUN_BOUNDED_CALL": "run_bounded(lambda: handler(task))",
    "V27_TIMEOUT_ERROR": "TimeoutError",
    "V35_FENCE_MARKER": "V35_1_FENCED_HANDLER_CALL",
    "V35_GUARD_CLASS": "LeaseExecutionGuard",
    "V35_GUARD_EXECUTE": "_v35_guard.execute",
}
missing = [name for name, token in required_contracts.items() if token not in patched]
print("CONTRACT_MISSING=", missing)

if missing:
    shutil.copy2(BACKUP, SRC)
    py_compile.compile(str(SRC), doraise=True)
    print("SOURCE_RESTORED=TRUE")
    raise SystemExit("V65_66_ABORT=contract_proof_failed")

print("DUAL_CONTRACT_PROOF=PASS")

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

# Prove both historical contracts independently.
rc27 = run(
    "V27_TIMEOUT_CONTRACT_TEST",
    [sys.executable, "-m", "pytest", "-q", str(T27)],
    120,
)
rc35 = run(
    "V35_FENCED_CALL_CONTRACT_TEST",
    [sys.executable, "-m", "pytest", "-q", str(T35)],
    120,
)

if rc27 != 0 or rc35 != 0:
    shutil.copy2(BACKUP, SRC)
    py_compile.compile(str(SRC), doraise=True)
    print("TARGET_CONTRACT_TESTS=FAIL")
    print("SOURCE_RESTORED=TRUE")
    raise SystemExit(1)

print("TARGET_CONTRACT_TESTS=PASS")

# Run all dispatch-related tests to catch any other historical contract drift.
dispatcher_tests = sorted(
    str(p.relative_to(ROOT))
    for p in (ROOT / "tests").glob("*dispatch*.py")
    if p.is_file()
)

print("DISPATCHER_TEST_FILES=", dispatcher_tests)

if dispatcher_tests:
    rc = run(
        "ALL_DISPATCHER_TESTS",
        [sys.executable, "-m", "pytest", "-q", *dispatcher_tests],
        300,
    )
    if rc != 0:
        shutil.copy2(BACKUP, SRC)
        py_compile.compile(str(SRC), doraise=True)
        print("ALL_DISPATCHER_TESTS=FAIL")
        print("SOURCE_RESTORED=TRUE")
        raise SystemExit(rc)

print("ALL_DISPATCHER_TESTS=PASS")

# Resume full-suite scan.
OUT = Path.home() / ".companyos_runtime/tmp" / f"v65_66_fullsuite_{int(time.time())}.out"
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
    print("V65_66_READY_FOR_CHECKPOINT=TRUE")
else:
    print("FULL_SUITE=NEXT_FAILURE_FOUND")
    print("V65_66_READY_FOR_CHECKPOINT=DISPATCH_ONLY")

print("SOURCE_RESTORED=FALSE")
print("V65_66_COMPLETE")
PY
