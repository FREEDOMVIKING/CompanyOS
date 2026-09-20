#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.53 MANIFEST IDENTITY SINGLE-LINE FIX ====="

python - <<'PY'
from pathlib import Path
import ast, shutil, time, py_compile, subprocess, sys, tempfile, importlib.util

ROOT = Path.home() / "companyos"
SRC = ROOT / "companyos/runtime/capability_expansion.py"
BACKUP = SRC.with_name(f"capability_expansion.py.v65_53_backup_{int(time.time())}")

# Prove the V65.52 auto-restore really left us on healthy source.
try:
    py_compile.compile(str(SRC), doraise=True)
    print("BASELINE_COMPILE=PASS")
except Exception as exc:
    print("BASELINE_COMPILE=FAIL", repr(exc))
    raise SystemExit("V65_53_ABORT=current_source_not_compileable")

text = SRC.read_text()
shutil.copy2(SRC, BACKUP)
print("BACKUP=", BACKUP)

tree = ast.parse(text)
stage = next(
    (n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "stage_plan"),
    None,
)
if stage is None:
    raise SystemExit("V65_53_ABORT=stage_plan_not_found")

# Locate the existing cid assignment that follows generated-source normalization.
cid_assign = None
for n in stage.body:
    if isinstance(n, ast.Assign):
        if any(isinstance(t, ast.Name) and t.id == "cid" for t in n.targets):
            cid_assign = n
            break
if cid_assign is None:
    raise SystemExit("V65_53_ABORT=cid_assignment_not_found")

lines = text.splitlines(keepends=True)
idx = cid_assign.lineno - 1
indent = lines[idx][:len(lines[idx]) - len(lines[idx].lstrip())]
marker = "V65.53: canonicalize capability_manifest id before staging"

print("CID_ASSIGN_LINE=", cid_assign.lineno)
print("CID_ASSIGN_SOURCE=", lines[idx].rstrip())

if marker not in text:
    # Intentionally one physical Python statement at the same indentation as cid=.
    # This avoids the indentation regressions from V65.51/V65.52.
    fix = (
        indent + "# " + marker + "\n" +
        indent +
        "module_content = re.sub("
        "r\"(?s)(def\\s+capability_manifest\\s*\\([^)]*\\)\\s*:\\s*return\\s*\\{.*?['\\\"]id['\\\"]\\s*:\\s*)['\\\"][^'\\\"]*['\\\"]\", "
        "lambda m: m.group(1) + repr(canonical_id), "
        "module_content, count=1) if module_content is not None else module_content\n"
    )
    lines[idx:idx] = [fix]
    SRC.write_text("".join(lines))
    print("PATCH_STATUS=inserted_before_cid")
else:
    print("PATCH_STATUS=already_present")

try:
    py_compile.compile(str(SRC), doraise=True)
    print("PATCH_COMPILE=PASS")
except Exception:
    shutil.copy2(BACKUP, SRC)
    py_compile.compile(str(SRC), doraise=True)
    print("PATCH_COMPILE=FAIL")
    print("SOURCE_RESTORED=TRUE")
    raise

# Show the exact patch context.
patched_lines = SRC.read_text().splitlines()
print("PATCH_CONTEXT_BEGIN")
for i, line in enumerate(patched_lines, 1):
    if marker in line:
        for j in range(max(1, i-5), min(len(patched_lines), i+5)+1):
            print(f"{j:04d}: {patched_lines[j-1]}")
        break
print("PATCH_CONTEXT_END")

def run(label, args, timeout=180):
    cp = subprocess.run(args, cwd=str(ROOT), text=True, capture_output=True, timeout=timeout)
    print(f"\n===== {label} =====")
    print("RETURN_CODE=", cp.returncode)
    if cp.stdout:
        print(cp.stdout[-16000:])
    if cp.stderr:
        print(cp.stderr[-6000:])
    return cp.returncode

# Full canonical capability-expansion suite.
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

# Direct sandbox proof of generated identity + metadata + stage execution.
import companyos.runtime.capability_expansion as ce

plan = {
    "gap": {
        "id": "research_quality_analyzer",
        "title": "Research quality analyzer",
        "reason": "V65.53 identity consistency proof",
    },
    "changes": [
        {
            "path": "whatever.py",
            "content": (
                "CAPABILITY_ID='placeholder_id'\n"
                "def capability_manifest(): return {'id':'placeholder_id','kind':'analysis'}\n"
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
            raise SystemExit("V65_53_ABORT=proof_stage_errors")

        normalized = ce.normalize_capability_id(plan["gap"]["id"])
        module_rel, _ = ce.canonical_paths(normalized)
        staged_module = Path(staged_root) / module_rel

        spec = importlib.util.spec_from_file_location("v65_53_probe", staged_module)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        cap_id = getattr(mod, "CAPABILITY_ID", None)
        manifest = mod.capability_manifest()
        manifest_id = manifest.get("id") if isinstance(manifest, dict) else None
        manifest_kind = manifest.get("kind") if isinstance(manifest, dict) else None

        print("PROOF_CAPABILITY_ID=", cap_id)
        print("PROOF_MANIFEST_ID=", manifest_id)
        print("PROOF_MANIFEST_KIND=", manifest_kind)

        if cap_id != normalized:
            raise SystemExit("V65_53_ABORT=capability_id_not_canonical")
        if manifest_id != normalized:
            raise SystemExit("V65_53_ABORT=manifest_id_not_canonical")
        if manifest_kind != "analysis":
            raise SystemExit("V65_53_ABORT=manifest_metadata_lost")

        ok, steps = ce.test_stage(Path(staged_root), normalized)
        print("PROOF_TEST_STAGE_OK=", ok)
        if not ok:
            print("PROOF_TEST_STAGE_STEPS=", steps)
            raise SystemExit("V65_53_ABORT=test_stage_failed")

        print("GENERATED_IDENTITY_CONSISTENCY=PASS")
        print("MANIFEST_METADATA_PRESERVED=PASS")
        print("STAGED_EXECUTION_PROOF=PASS")
finally:
    ce.ROOT, ce.STAGING = old_root, old_staging

print("SOURCE_RESTORED=FALSE")
print("V65_53_STABILITY_GATE=PASS")
print("V65_53_COMPLETE")
PY
