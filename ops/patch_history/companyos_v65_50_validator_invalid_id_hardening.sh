#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.50 VALIDATOR INVALID-ID HARDENING ====="

python - <<'PY'
from pathlib import Path
import ast, shutil, time, py_compile, subprocess, sys, tempfile, json

ROOT = Path.home() / "companyos"
SRC = ROOT / "companyos/runtime/capability_expansion.py"
BACKUP = SRC.with_name(f"capability_expansion.py.v65_50_backup_{int(time.time())}")

text = SRC.read_text()
shutil.copy2(SRC, BACKUP)
print("BACKUP=", BACKUP)

tree = ast.parse(text)
fn = next(
    (n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "validate_source"),
    None,
)
if fn is None:
    raise SystemExit("V65_50_ABORT=validate_source_not_found")

lines = text.splitlines(keepends=True)
target_idx = None
for i in range(fn.lineno - 1, fn.end_lineno):
    if "expected=set(canonical_paths(gap_id))" in lines[i].replace(" ", ""):
        target_idx = i
        break

# Fallback tolerant lookup preserving local formatting.
if target_idx is None:
    for i in range(fn.lineno - 1, fn.end_lineno):
        compact = "".join(lines[i].split())
        if compact == "expected=set(canonical_paths(gap_id))":
            target_idx = i
            break

if target_idx is None:
    print("VALIDATE_SOURCE_CONTEXT_BEGIN")
    for i in range(fn.lineno - 1, min(fn.end_lineno, fn.lineno + 25)):
        print(f"{i+1:04d}: {lines[i].rstrip()}")
    print("VALIDATE_SOURCE_CONTEXT_END")
    raise SystemExit("V65_50_ABORT=expected_path_line_not_found")

indent = lines[target_idx][:len(lines[target_idx]) - len(lines[target_idx].lstrip())]
marker = "V65.50: malformed candidate ids are validation findings, not exceptions"

if marker not in text:
    replacement = [
        indent + "# " + marker + "\n",
        indent + "try:\n",
        indent + " expected=set(canonical_paths(gap_id))\n",
        indent + "except (ValueError, TypeError):\n",
        indent + " expected=set()\n",
        indent + ' errors.append("invalid_capability_id")\n',
    ]
    lines[target_idx:target_idx+1] = replacement
    SRC.write_text("".join(lines))
    print("PATCH_STATUS=inserted")
else:
    print("PATCH_STATUS=already_present")

try:
    py_compile.compile(str(SRC), doraise=True)
    print("PY_COMPILE=PASS")
except Exception:
    shutil.copy2(BACKUP, SRC)
    print("PY_COMPILE=FAIL")
    print("SOURCE_RESTORED=TRUE")
    raise

def run(label, args, timeout=180):
    cp = subprocess.run(args, cwd=str(ROOT), text=True, capture_output=True, timeout=timeout)
    print(f"\n===== {label} =====")
    print("RETURN_CODE=", cp.returncode)
    if cp.stdout:
        print(cp.stdout[-16000:])
    if cp.stderr:
        print(cp.stderr[-6000:])
    return cp.returncode

# Exact regression exposed by V65.49.
v3 = ROOT / "tests/test_capability_expansion_v3.py"
rc = run(
    "V3_NETWORK_REGRESSION",
    [sys.executable, "-m", "pytest", "-q",
     str(v3) + "::CapabilityExpansionV3Tests::test_blocks_network"],
    90,
)
if rc != 0:
    shutil.copy2(BACKUP, SRC)
    py_compile.compile(str(SRC), doraise=True)
    print("V3_NETWORK_REGRESSION=FAIL")
    print("SOURCE_RESTORED=TRUE")
    raise SystemExit(rc)
print("V3_NETWORK_REGRESSION=PASS")

# Run all canonical capability-expansion tests from tests/ only.
tests = sorted(
    p for p in (ROOT / "tests").glob("test_capability_expansion*.py")
    if ".bak" not in p.name and "backup" not in p.name
)
overall = True
for test in tests:
    rc = run("PYTEST::" + test.name, [sys.executable, "-m", "pytest", "-q", str(test)])
    overall = overall and (rc == 0)

if not overall:
    shutil.copy2(BACKUP, SRC)
    py_compile.compile(str(SRC), doraise=True)
    print("CAPABILITY_SUITE=FAIL")
    print("SOURCE_RESTORED=TRUE")
    raise SystemExit(1)

print("CAPABILITY_SUITE=PASS")

# Corrected V65.49 proof: no package import in the generated test.
# We only need stage_plan to write the module, then inspect the staged module
# to prove placeholder CAPABILITY_ID was canonicalized.
import companyos.runtime.capability_expansion as ce

plan = {
    "gap": {
        "id": "research_quality_analyzer",
        "title": "Research quality analyzer",
        "reason": "V65.50 canonical-id proof",
    },
    "changes": [
        {
            "path": "whatever.py",
            "content": (
                "CAPABILITY_ID='placeholder_id'\n"
                "def capability_manifest(): return {'id':'placeholder_id'}\n"
                "def evaluate(context): return {'ok':True}\n"
            ),
        },
        {
            "path": "tests/generated/test_x.py",
            "content": (
                "import unittest\n"
                "class T(unittest.TestCase):\n"
                "    def test_ok(self): self.assertTrue(True)\n"
            ),
        },
    ],
}

old_root, old_staging = ce.ROOT, ce.STAGING
try:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        ce.ROOT = root
        ce.STAGING = root / ".companyos" / "capability_expansion" / "staging"

        cid, staged_root, errors = ce.stage_plan(plan["gap"], plan)
        print("PROOF_CID=", cid)
        print("PROOF_STAGE_ERRORS=", errors)
        if errors:
            raise SystemExit("V65_50_ABORT=proof_stage_errors")

        module_rel, _ = ce.canonical_paths(plan["gap"]["id"])
        staged_module = Path(staged_root) / module_rel
        content = staged_module.read_text()
        print("PROOF_MODULE=", staged_module)
        print("PROOF_CONTENT_BEGIN")
        print(content)
        print("PROOF_CONTENT_END")

        canonical_ok = (
            "CAPABILITY_ID='research_quality_analyzer'" in content
            or 'CAPABILITY_ID="research_quality_analyzer"' in content
        )
        print("CANONICAL_ID_STAGE_PROOF=", "PASS" if canonical_ok else "FAIL")
        if not canonical_ok:
            raise SystemExit("V65_50_ABORT=canonical_id_proof_failed")
finally:
    ce.ROOT, ce.STAGING = old_root, old_staging

print("SOURCE_RESTORED=FALSE")
print("V65_50_STABILITY_GATE=PASS")
print("V65_50_COMPLETE")
PY
