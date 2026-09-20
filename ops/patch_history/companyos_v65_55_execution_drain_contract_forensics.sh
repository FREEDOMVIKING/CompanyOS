#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
export GIT_PAGER=cat
export PAGER=cat

echo "===== COMPANYOS V65.55 EXECUTION DRAIN CONTRACT FORENSICS ====="
echo "SOURCE_WRITES=0"

python - <<'PY'
from pathlib import Path
import ast, inspect, subprocess, sys, json, time

ROOT = Path.home() / "companyos"
SRC = ROOT / "companyos/runtime/execution_drain_engine.py"
TEST = ROOT / "tests/test_execution_drain_engine.py"
REPORT_DIR = Path.home() / ".companyos_runtime/reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

print("SOURCE=", SRC)
print("TEST=", TEST)

if not SRC.exists():
    raise SystemExit("V65_55_ABORT=source_missing")
if not TEST.exists():
    raise SystemExit("V65_55_ABORT=test_missing")

src_text = SRC.read_text()
test_text = TEST.read_text()

ast.parse(src_text)
ast.parse(test_text)
print("SOURCE_AST=PASS")
print("TEST_AST=PASS")

import companyos.runtime.execution_drain_engine as ede
print("ENGINE_SIGNATURE=", inspect.signature(ede.ExecutionDrainEngine))
print("INIT_SIGNATURE=", inspect.signature(ede.ExecutionDrainEngine.__init__))

print("\n===== ENGINE SOURCE =====")
print(src_text)

print("\n===== TEST SOURCE =====")
print(test_text)

print("\n===== ALL EXECUTIONDRAINENGINE REFERENCES =====")
refs = []
for base in [ROOT / "companyos", ROOT / "tests"]:
    for p in sorted(base.rglob("*.py")):
        # Skip caches/backups/generated snapshots.
        ps = str(p)
        if "__pycache__" in ps or ".v65_" in p.name or ".bak" in p.name or "backup" in p.name:
            continue
        try:
            lines = p.read_text(errors="ignore").splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines, 1):
            if "ExecutionDrainEngine" in line:
                item = f"{p.relative_to(ROOT)}:{i}: {line.strip()}"
                refs.append(item)
                print(item)

print("\n===== BATCH-SIZE / DISPATCHER CONTRACT REFERENCES =====")
contract_refs = []
needles = ("batch_size", "live_dependency_dispatcher_required", "dispatch_next")
for base in [ROOT / "companyos/runtime", ROOT / "tests"]:
    for p in sorted(base.rglob("*.py")):
        ps = str(p)
        if "__pycache__" in ps or ".v65_" in p.name or ".bak" in p.name or "backup" in p.name:
            continue
        try:
            lines = p.read_text(errors="ignore").splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines, 1):
            if any(n in line for n in needles):
                # Keep this diagnostic focused on drain/execution context.
                lower = str(p).lower() + " " + line.lower()
                if "drain" in lower or "dispatcher" in lower or "batch_size" in lower:
                    item = f"{p.relative_to(ROOT)}:{i}: {line.strip()}"
                    contract_refs.append(item)
                    print(item)

print("\n===== TARGETED TEST =====")
cp = subprocess.run(
    [sys.executable, "-m", "pytest", "-q", str(TEST)],
    cwd=str(ROOT),
    text=True,
    capture_output=True,
    timeout=90,
)
print("RETURN_CODE=", cp.returncode)
print("STDOUT_BEGIN")
print(cp.stdout[-12000:])
print("STDOUT_END")
print("STDERR_BEGIN")
print(cp.stderr[-4000:])
print("STDERR_END")

report = {
    "version": "V65.55",
    "timestamp": int(time.time()),
    "source_writes": 0,
    "engine_signature": str(inspect.signature(ede.ExecutionDrainEngine)),
    "init_signature": str(inspect.signature(ede.ExecutionDrainEngine.__init__)),
    "references": refs,
    "contract_references": contract_refs,
    "targeted_test_returncode": cp.returncode,
}
rp = REPORT_DIR / f"v65_55_execution_drain_contract_{report['timestamp']}.json"
rp.write_text(json.dumps(report, indent=2))

print("REPORT=", rp)
print("V65_55_FORENSICS=COMPLETE")
PY
