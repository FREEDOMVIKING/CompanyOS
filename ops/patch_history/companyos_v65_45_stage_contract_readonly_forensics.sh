#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.45 STAGE CONTRACT READ-ONLY FORENSICS ====="

python - <<'PY'
from pathlib import Path
import ast, inspect, json, time

ROOT = Path.home() / "companyos"
SRC = ROOT / "companyos/runtime/capability_expansion.py"
TEST = ROOT / "tests/test_capability_expansion_test_recovery_v5.py"
REPORT_DIR = Path.home() / ".companyos_runtime/reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

print("SOURCE =", SRC)
print("TEST   =", TEST)
print("WRITES_TO_SOURCE=0")

if not SRC.exists():
    raise SystemExit("V65_45_ABORT=source_missing")
if not TEST.exists():
    raise SystemExit("V65_45_ABORT=test_missing")

source_text = SRC.read_text()
test_text = TEST.read_text()

# Parse only. No source mutation.
try:
    tree = ast.parse(source_text)
    print("SOURCE_AST=PASS")
except Exception as e:
    print("SOURCE_AST=FAIL", repr(e))
    raise

try:
    test_tree = ast.parse(test_text)
    print("TEST_AST=PASS")
except Exception as e:
    print("TEST_AST=FAIL", repr(e))
    raise

def function_source(text, tree, name):
    lines = text.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            start = node.lineno
            end = getattr(node, "end_lineno", start)
            return "\n".join(f"{i:04d}: {lines[i-1]}" for i in range(start, end+1))
    return None

print("\n===== CURRENT stage_plan() =====")
sp = function_source(source_text, tree, "stage_plan")
print(sp or "NOT_FOUND")

print("\n===== CURRENT test_stage() =====")
ts = function_source(source_text, tree, "test_stage")
print(ts or "NOT_FOUND")

print("\n===== FAILING TEST METHOD =====")
tm = function_source(test_text, test_tree, "test_staged_contract_executes")
print(tm or "NOT_FOUND")

# Inspect assertions/calls in failing test.
target = None
for node in ast.walk(test_tree):
    if isinstance(node, ast.FunctionDef) and node.name == "test_staged_contract_executes":
        target = node
        break

calls, assertions = [], []
if target:
    for n in ast.walk(target):
        if isinstance(n, ast.Call):
            try:
                calls.append(ast.unparse(n))
            except Exception:
                pass
        if isinstance(n, ast.Assert):
            try:
                assertions.append(ast.unparse(n.test))
            except Exception:
                pass

print("\n===== TEST CONTRACT =====")
print("CALLS=")
for x in calls:
    print(" ", x)
print("ASSERTIONS=")
for x in assertions:
    print(" ", x)

# Import current module and inspect signatures only.
print("\n===== RUNTIME SIGNATURES =====")
try:
    import companyos.runtime.capability_expansion as ce
    for name in ("stage_plan", "test_stage"):
        obj = getattr(ce, name, None)
        print(name, "EXISTS=", obj is not None,
              "SIGNATURE=", str(inspect.signature(obj)) if obj else None)
except Exception as e:
    print("IMPORT_ERROR=", repr(e))

# Run exactly the one failing test, without editing anything.
print("\n===== TARGETED TEST =====")
import subprocess, sys
cp = subprocess.run(
    [sys.executable, "-m", "pytest", "-q",
     str(TEST) + "::CapabilityExpansionTestRecoveryV5::test_staged_contract_executes"],
    cwd=str(ROOT), text=True, capture_output=True, timeout=90
)
print("RETURN_CODE=", cp.returncode)
print("STDOUT_BEGIN")
print(cp.stdout[-12000:])
print("STDOUT_END")
print("STDERR_BEGIN")
print(cp.stderr[-6000:])
print("STDERR_END")

report = {
    "timestamp": int(time.time()),
    "source": str(SRC),
    "test": str(TEST),
    "source_ast": True,
    "calls": calls,
    "assertions": assertions,
    "targeted_test_returncode": cp.returncode,
    "source_writes": 0,
}
rp = REPORT_DIR / f"v65_45_stage_contract_forensics_{report['timestamp']}.json"
rp.write_text(json.dumps(report, indent=2))
print("REPORT=", rp)
print("V65_45_FORENSICS=COMPLETE")
PY
