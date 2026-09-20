#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
export GIT_PAGER=cat
export PAGER=cat

echo "===== COMPANYOS V65.57 INTEGRITY GUARD CONTRACT FORENSICS ====="
echo "SOURCE_WRITES=0"

python - <<'PY'
from pathlib import Path
import ast, inspect, subprocess, sys, json, time, importlib.util

ROOT = Path.home() / "companyos"
REPORT_DIR = Path.home() / ".companyos_runtime/reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

matches = []
for base in [ROOT / "companyos", ROOT / "tests"]:
    for p in sorted(base.rglob("*.py")):
        ps = str(p)
        if "__pycache__" in ps or ".v65_" in p.name or ".bak" in p.name or "backup" in p.name:
            continue
        try:
            txt = p.read_text(errors="ignore")
        except Exception:
            continue
        if "DataIntegrityGuard" in txt:
            matches.append((p, txt))

print("MATCHING_FILES=", [str(p.relative_to(ROOT)) for p,_ in matches])

class_file = None
class_node = None
class_text = None

for p, txt in matches:
    try:
        tree = ast.parse(txt)
    except Exception:
        continue
    for n in tree.body:
        if isinstance(n, ast.ClassDef) and n.name == "DataIntegrityGuard":
            class_file = p
            class_node = n
            class_text = txt
            break
    if class_file:
        break

if class_file is None:
    raise SystemExit("V65_57_ABORT=DataIntegrityGuard_class_not_found")

print("CLASS_FILE=", class_file.relative_to(ROOT))
print("CLASS_LINE=", class_node.lineno)

lines = class_text.splitlines()
print("\n===== CLASS SOURCE =====")
for i in range(class_node.lineno, class_node.end_lineno + 1):
    print(f"{i:04d}: {lines[i-1]}")

# Import directly from file, avoiding assumptions about module path.
rel = class_file.relative_to(ROOT).with_suffix("")
modname = ".".join(rel.parts)
mod = __import__(modname, fromlist=["DataIntegrityGuard"])
Guard = getattr(mod, "DataIntegrityGuard")

print("\n===== RUNTIME CONTRACT =====")
print("CLASS_SIGNATURE=", inspect.signature(Guard))
for name in ("__init__", "validate", "evaluate"):
    obj = getattr(Guard, name, None)
    print(name, "EXISTS=", obj is not None,
          "SIGNATURE=", str(inspect.signature(obj)) if obj else None)

print("\n===== REFERENCES =====")
refs = []
for p, txt in matches:
    for i, line in enumerate(txt.splitlines(), 1):
        if "DataIntegrityGuard" in line or ".validate(" in line or ".evaluate(" in line:
            item = f"{p.relative_to(ROOT)}:{i}: {line.strip()}"
            refs.append(item)
            print(item)

# Show the exact failing test around test_integrity.
test_candidates = []
for p in (ROOT / "tests").rglob("*.py"):
    try:
        txt = p.read_text(errors="ignore")
    except Exception:
        continue
    if "def test_integrity" in txt and "DataIntegrityGuard" in txt:
        test_candidates.append((p, txt))

print("\n===== FAILING TEST SOURCE =====")
for p, txt in test_candidates:
    tree = ast.parse(txt)
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == "test_integrity":
            print("TEST_FILE=", p.relative_to(ROOT))
            ls = txt.splitlines()
            for i in range(n.lineno, n.end_lineno + 1):
                print(f"{i:04d}: {ls[i-1]}")

print("\n===== DIRECT PROBE =====")
g = Guard()
if hasattr(g, "validate"):
    try:
        rv = g.validate({"name":"x","passed":True})
        print("VALIDATE_RESULT=", repr(rv))
    except Exception as e:
        print("VALIDATE_ERROR=", type(e).__name__, str(e))
if hasattr(g, "evaluate"):
    try:
        rv = g.evaluate({"name":"x","passed":True})
        print("EVALUATE_RESULT=", repr(rv))
    except Exception as e:
        print("EVALUATE_ERROR=", type(e).__name__, str(e))
else:
    print("EVALUATE_MISSING=True")

print("\n===== TARGETED TEST =====")
target = ROOT / "tests/test_phase1501_12000.py"
cp = subprocess.run(
    [sys.executable, "-m", "pytest", "-q", str(target) + "::test_integrity"],
    cwd=str(ROOT), text=True, capture_output=True, timeout=90
)
print("RETURN_CODE=", cp.returncode)
print(cp.stdout[-10000:])
print(cp.stderr[-4000:])

report = {
    "version": "V65.57",
    "timestamp": int(time.time()),
    "source_writes": 0,
    "class_file": str(class_file.relative_to(ROOT)),
    "class_signature": str(inspect.signature(Guard)),
    "has_validate": hasattr(Guard, "validate"),
    "has_evaluate": hasattr(Guard, "evaluate"),
    "references": refs,
    "targeted_test_returncode": cp.returncode,
}
rp = REPORT_DIR / f"v65_57_integrity_guard_contract_{report['timestamp']}.json"
rp.write_text(json.dumps(report, indent=2))

print("REPORT=", rp)
print("V65_57_FORENSICS=COMPLETE")
PY
