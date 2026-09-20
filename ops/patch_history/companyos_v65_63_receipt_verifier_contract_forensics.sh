#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
export GIT_PAGER=cat
export PAGER=cat

echo "===== COMPANYOS V65.63 RECEIPT VERIFIER CONTRACT FORENSICS ====="
echo "SOURCE_WRITES=0"

python - <<'PY'
from pathlib import Path
import ast, inspect, importlib, json, subprocess, sys, time

ROOT = Path.home() / "companyos"
REPORT_DIR = Path.home() / ".companyos_runtime/reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Find exact failing test dynamically.
test_file = None
test_text = None
test_fn = None

for p in sorted((ROOT / "tests").rglob("*.py")):
    try:
        txt = p.read_text(errors="ignore")
        tree = ast.parse(txt)
    except Exception:
        continue
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == "test_receipt_verification":
            test_file = p
            test_text = txt
            test_fn = n
            break
    if test_file:
        break

if test_file is None:
    raise SystemExit("V65_63_ABORT=test_receipt_verification_not_found")

print("TARGET_TEST_FILE=", test_file.relative_to(ROOT))
print("TARGET_TEST_LINE=", test_fn.lineno)

print("\n===== FAILING TEST SOURCE =====")
lines = test_text.splitlines()
for i in range(max(1, test_fn.lineno - 10), min(len(lines), test_fn.end_lineno + 10) + 1):
    print(f"{i:04d}: {lines[i-1]}")

# Resolve the imported verifier class/module from the test.
tree = ast.parse(test_text)
verifier_module = None
verifier_name = "OnChainReceiptVerifier"

for n in tree.body:
    if isinstance(n, ast.ImportFrom) and n.module:
        imported = {a.name for a in n.names}
        if verifier_name in imported:
            verifier_module = n.module
            break

print("VERIFIER_MODULE=", verifier_module)

if not verifier_module:
    # Fallback: locate class definition in repo.
    for p in sorted((ROOT / "companyos").rglob("*.py")):
        try:
            txt = p.read_text(errors="ignore")
            tr = ast.parse(txt)
        except Exception:
            continue
        if any(isinstance(n, ast.ClassDef) and n.name == verifier_name for n in tr.body):
            rel = p.relative_to(ROOT).with_suffix("")
            verifier_module = ".".join(rel.parts)
            break

if not verifier_module:
    raise SystemExit("V65_63_ABORT=verifier_module_not_found")

mod = importlib.import_module(verifier_module)
Verifier = getattr(mod, verifier_name)
src_path = Path(inspect.getsourcefile(Verifier) or "")

print("RESOLVED_VERIFIER_MODULE=", verifier_module)
print("RESOLVED_VERIFIER_SOURCE=", src_path)
print("VERIFIER_SIGNATURE=", inspect.signature(Verifier))

print("\n===== VERIFIER CLASS SOURCE =====")
print(inspect.getsource(Verifier))

verify_fn = getattr(Verifier, "verify", None)
if verify_fn is None:
    raise SystemExit("V65_63_ABORT=verify_method_missing")

print("VERIFY_SIGNATURE=", inspect.signature(verify_fn))
print("\n===== VERIFY SOURCE =====")
print(inspect.getsource(verify_fn))

# Find every repo reference to verifier / passed / signature around receipt code.
print("\n===== RECEIPT VERIFIER REFERENCES =====")
refs = []
needles = ("OnChainReceiptVerifier", ".verify(", "signature", "\"passed\"", "'passed'")
for base in [ROOT / "companyos", ROOT / "tests"]:
    for p in sorted(base.rglob("*.py")):
        ps = str(p)
        if "__pycache__" in ps or ".v65_" in p.name or ".bak" in p.name or "backup" in p.name:
            continue
        try:
            pls = p.read_text(errors="ignore").splitlines()
        except Exception:
            continue
        for i, line in enumerate(pls, 1):
            if any(n in line for n in needles):
                low = (str(p) + " " + line).lower()
                if "receipt" in low or "signature" in low or "onchainreceiptverifier" in low:
                    item = f"{p.relative_to(ROOT)}:{i}: {line.strip()}"
                    refs.append(item)
                    print(item)

print("\n===== DIRECT PROBES =====")
v = Verifier()

probe_inputs = [
    {"success": True, "signature": "abc"},
    {"success": True, "signature": "abc", "txid": "abc"},
    {"success": False, "signature": "abc"},
    {"signature": "abc"},
    {"success": True},
]

probe_results = []
for payload in probe_inputs:
    try:
        result = v.verify(dict(payload))
        print("INPUT=", payload)
        print("RESULT=", repr(result))
        probe_results.append({"input": payload, "result": result})
    except Exception as exc:
        print("INPUT=", payload)
        print("ERROR=", type(exc).__name__, str(exc))
        probe_results.append({"input": payload, "error": f"{type(exc).__name__}: {exc}"})

print("\n===== TARGETED TEST =====")
node = f"{test_file}::test_receipt_verification"
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
    "version": "V65.63",
    "timestamp": int(time.time()),
    "source_writes": 0,
    "target_test_file": str(test_file.relative_to(ROOT)),
    "verifier_module": verifier_module,
    "verifier_source": str(src_path),
    "verifier_signature": str(inspect.signature(Verifier)),
    "verify_signature": str(inspect.signature(verify_fn)),
    "references": refs,
    "probe_results": probe_results,
    "targeted_test_returncode": cp.returncode,
}
rp = REPORT_DIR / f"v65_63_receipt_verifier_contract_{report['timestamp']}.json"
rp.write_text(json.dumps(report, indent=2, default=str))

print("REPORT=", rp)
print("V65_63_FORENSICS=COMPLETE")
PY
