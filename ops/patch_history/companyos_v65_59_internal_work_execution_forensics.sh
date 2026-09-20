#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
export GIT_PAGER=cat
export PAGER=cat

echo "===== COMPANYOS V65.59 INTERNAL WORK EXECUTION FORENSICS ====="
echo "SOURCE_WRITES=0"

python - <<'PY'
from pathlib import Path
import ast, inspect, subprocess, sys, json, time, importlib

ROOT = Path.home() / "companyos"
REPORT_DIR = Path.home() / ".companyos_runtime/reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Find the exact failing test by function name.
target_file = None
target_func = None
target_text = None

for p in sorted((ROOT / "tests").rglob("*.py")):
    try:
        txt = p.read_text(errors="ignore")
        tree = ast.parse(txt)
    except Exception:
        continue
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == "test_internal_work_executes":
            target_file = p
            target_func = n
            target_text = txt
            break
    if target_file:
        break

if target_file is None:
    raise SystemExit("V65_59_ABORT=test_internal_work_executes_not_found")

print("TARGET_FILE=", target_file.relative_to(ROOT))
print("TARGET_FUNCTION_LINE=", target_func.lineno)

print("\n===== FAILING TEST SOURCE =====")
test_lines = target_text.splitlines()
lo = max(1, target_func.lineno - 12)
hi = min(len(test_lines), target_func.end_lineno + 12)
for i in range(lo, hi + 1):
    print(f"{i:04d}: {test_lines[i-1]}")

# Print imports and helper definitions from the same test file.
tree = ast.parse(target_text)
print("\n===== TEST IMPORTS / HELPERS =====")
for n in tree.body:
    if isinstance(n, (ast.Import, ast.ImportFrom)):
        seg = ast.get_source_segment(target_text, n)
        if seg:
            print(seg)
    elif isinstance(n, ast.FunctionDef) and n.name in {"kernel", "make_kernel", "_kernel"}:
        print(ast.get_source_segment(target_text, n) or "")

print("\n===== RELEVANT SYMBOL REFERENCES =====")
needles = (
    "executed_count",
    "run_cycle(",
    "def run_cycle",
    "def enqueue",
    "class ",
    "capabilities",
    "work_type",
    "internal",
)
refs = []
for base in [ROOT / "companyos", ROOT / "tests"]:
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
                low = (str(p) + " " + line).lower()
                if "executed_count" in low or "run_cycle" in low or "internal" in low:
                    item = f"{p.relative_to(ROOT)}:{i}: {line.strip()}"
                    refs.append(item)
                    print(item)

# Resolve imported runtime modules from the test file and inspect likely classes.
print("\n===== RUNTIME CLASS / SIGNATURE PROBES =====")
modules = []
for n in tree.body:
    if isinstance(n, ast.ImportFrom) and n.module and n.module.startswith("companyos"):
        modules.append(n.module)
    elif isinstance(n, ast.Import):
        for alias in n.names:
            if alias.name.startswith("companyos"):
                modules.append(alias.name)

seen = set()
runtime_contracts = []
for modname in modules:
    if modname in seen:
        continue
    seen.add(modname)
    try:
        mod = importlib.import_module(modname)
    except Exception as exc:
        print("IMPORT_ERROR", modname, type(exc).__name__, str(exc))
        continue
    print("MODULE=", modname)
    for name, obj in sorted(vars(mod).items()):
        if inspect.isclass(obj) and getattr(obj, "__module__", "") == modname:
            methods = {}
            for m in ("__init__", "enqueue", "run_cycle", "execute", "evaluate"):
                fn = getattr(obj, m, None)
                if fn is not None:
                    try:
                        methods[m] = str(inspect.signature(fn))
                    except Exception:
                        methods[m] = "<unavailable>"
            if methods:
                print("CLASS=", name, "METHODS=", methods)
                runtime_contracts.append({"module":modname,"class":name,"methods":methods})

print("\n===== TARGETED TEST =====")
node = f"{target_file}::test_internal_work_executes"
cp = subprocess.run(
    [sys.executable, "-m", "pytest", "-q", node],
    cwd=str(ROOT),
    text=True,
    capture_output=True,
    timeout=120,
)
print("RETURN_CODE=", cp.returncode)
print("STDOUT_BEGIN")
print(cp.stdout[-14000:])
print("STDOUT_END")
print("STDERR_BEGIN")
print(cp.stderr[-5000:])
print("STDERR_END")

report = {
    "version": "V65.59",
    "timestamp": int(time.time()),
    "source_writes": 0,
    "target_file": str(target_file.relative_to(ROOT)),
    "target_line": target_func.lineno,
    "references": refs,
    "runtime_contracts": runtime_contracts,
    "targeted_test_returncode": cp.returncode,
}
rp = REPORT_DIR / f"v65_59_internal_work_execution_{report['timestamp']}.json"
rp.write_text(json.dumps(report, indent=2))

print("REPORT=", rp)
print("V65_59_FORENSICS=COMPLETE")
PY
