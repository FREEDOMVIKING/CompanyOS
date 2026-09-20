#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.48 AST-LOCATED CAPABILITY-ID FIX ====="

python - <<'PY'
from pathlib import Path
import ast, shutil, time, py_compile, subprocess, sys

ROOT = Path.home() / "companyos"
SRC = ROOT / "companyos/runtime/capability_expansion.py"
TEST = ROOT / "tests/test_capability_expansion_test_recovery_v5.py"
BACKUP = SRC.with_name(f"capability_expansion.py.v65_48_backup_{int(time.time())}")

text = SRC.read_text()
shutil.copy2(SRC, BACKUP)
print("BACKUP=", BACKUP)

tree = ast.parse(text)
stage = next(
    (n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "stage_plan"),
    None,
)
if stage is None:
    raise SystemExit("V65_48_ABORT=stage_plan_not_found")

target_line = None
for n in ast.walk(stage):
    if isinstance(n, ast.Call):
        fn = n.func
        name = fn.id if isinstance(fn, ast.Name) else (
            fn.attr if isinstance(fn, ast.Attribute) else None
        )
        if name == "_classify_generated_contents":
            target_line = n.lineno
            break

if target_line is None:
    raise SystemExit("V65_48_ABORT=classifier_call_not_found")

lines = text.splitlines(keepends=True)
idx = target_line - 1
original = lines[idx]
indent = original[:len(original) - len(original.lstrip())]

print("CLASSIFIER_LINE_NUMBER=", target_line)
print("CLASSIFIER_LINE=", original.rstrip())

marker = "V65.48: enforce canonical CAPABILITY_ID"
if marker in text:
    print("PATCH_STATUS=already_present")
else:
    block = [
        indent + "# V65.48: enforce canonical CAPABILITY_ID in generated source.\n",
        indent + "canonical_id = normalize_capability_id(gap['id'])\n",
        indent + "if module_content is not None:\n",
        indent + "    _cap_id_re = re.compile(r'(?m)^CAPABILITY_ID\\s*=\\s*[^\\n]+$')\n",
        indent + "    if _cap_id_re.search(module_content):\n",
        indent + "        module_content = _cap_id_re.sub('CAPABILITY_ID=' + repr(canonical_id), module_content, count=1)\n",
        indent + "    else:\n",
        indent + "        module_content = 'CAPABILITY_ID=' + repr(canonical_id) + '\\n' + module_content\n",
    ]
    lines[idx+1:idx+1] = block
    SRC.write_text("".join(lines))
    print("PATCH_STATUS=inserted")

try:
    py_compile.compile(str(SRC), doraise=True)
    print("PY_COMPILE=PASS")
except Exception:
    shutil.copy2(BACKUP, SRC)
    print("PY_COMPILE=FAIL")
    print("SOURCE_RESTORED=TRUE")
    raise

# Show exact patched stage_plan area.
patched = SRC.read_text().splitlines()
lo = max(0, target_line - 3)
hi = min(len(patched), target_line + 12)
print("PATCH_CONTEXT_BEGIN")
for i in range(lo, hi):
    print(f"{i+1:04d}: {patched[i]}")
print("PATCH_CONTEXT_END")

def run(label, args, timeout):
    cp = subprocess.run(
        args, cwd=str(ROOT), text=True, capture_output=True, timeout=timeout
    )
    print(f"{label}_RETURN_CODE=", cp.returncode)
    if cp.stdout:
        print(cp.stdout[-14000:])
    if cp.stderr:
        print(cp.stderr[-6000:])
    return cp.returncode

target_node = (
    str(TEST)
    + "::CapabilityExpansionTestRecoveryV5::test_staged_contract_executes"
)

rc = run(
    "TARGET_TEST",
    [sys.executable, "-m", "pytest", "-q", target_node],
    90,
)
if rc != 0:
    shutil.copy2(BACKUP, SRC)
    py_compile.compile(str(SRC), doraise=True)
    print("TARGET_TEST=FAIL")
    print("SOURCE_RESTORED=TRUE")
    raise SystemExit(rc)

print("TARGET_TEST=PASS")

rc = run(
    "RECOVERY_V5",
    [sys.executable, "-m", "pytest", "-q", str(TEST)],
    120,
)
if rc != 0:
    shutil.copy2(BACKUP, SRC)
    py_compile.compile(str(SRC), doraise=True)
    print("RECOVERY_V5=FAIL")
    print("SOURCE_RESTORED=TRUE")
    raise SystemExit(rc)

print("RECOVERY_V5=PASS")
print("SOURCE_RESTORED=FALSE")
print("V65_48_COMPLETE")
PY
