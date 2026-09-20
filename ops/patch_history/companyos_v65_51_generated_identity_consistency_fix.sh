#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.51 GENERATED IDENTITY CONSISTENCY FIX ====="

python - <<'PY'
from pathlib import Path
import ast, shutil, time, py_compile, subprocess, sys, tempfile, importlib.util

ROOT = Path.home() / "companyos"
SRC = ROOT / "companyos/runtime/capability_expansion.py"
BACKUP = SRC.with_name(f"capability_expansion.py.v65_51_backup_{int(time.time())}")

text = SRC.read_text()
shutil.copy2(SRC, BACKUP)
print("BACKUP=", BACKUP)

tree = ast.parse(text)
stage = next(
    (n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "stage_plan"),
    None,
)
if stage is None:
    raise SystemExit("V65_51_ABORT=stage_plan_not_found")

lines = text.splitlines(keepends=True)

insert_idx = None
for i in range(stage.lineno - 1, stage.end_lineno):
    if "module_content = 'CAPABILITY_ID=' + repr(canonical_id) + '\\n' + module_content" in lines[i]:
        insert_idx = i + 1
        break

if insert_idx is None:
    raise SystemExit("V65_51_ABORT=v65_48_identity_block_not_found")

marker = "V65.51: keep capability_manifest()['id'] consistent with CAPABILITY_ID"

if marker not in text:
    indent = lines[insert_idx-1][:len(lines[insert_idx-1]) - len(lines[insert_idx-1].lstrip())]
    block = [
        indent + "# " + marker + "\n",
        indent + "_manifest_id_re = re.compile(\n",
        indent + '    r"(?s)(def\\s+capability_manifest\\s*\\([^)]*\\)\\s*:\\s*return\\s*\\{.*?[\\\'\\\"]id[\\\'\\\"]\\s*:\\s*)[\\\'\\\"][^\\\'\\\"]*[\\\'\\\"]"\n',
        indent + ")\n",
        indent + "module_content = _manifest_id_re.sub(\n",
        indent + "    lambda m: m.group(1) + repr(canonical_id),\n",
        indent + "    module_content,\n",
        indent + "    count=1,\n",
        indent + ")\n",
    ]
    lines[insert_idx:insert_idx] = block
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

import companyos.runtime.capability_expansion as ce

plan = {
    "gap": {
        "id": "research_quality_analyzer",
        "title": "Research quality analyzer",
        "reason": "V65.51 identity consistency proof",
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
            raise SystemExit("V65_51_ABORT=proof_stage_errors")

        module_rel, _ = ce.canonical_paths(plan["gap"]["id"])
        staged_module = Path(staged_root) / module_rel
        print("PROOF_MODULE=", staged_module)

        spec = importlib.util.spec_from_file_location("v65_51_generated_probe", staged_module)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        cap_id = getattr(mod, "CAPABILITY_ID", None)
        manifest = mod.capability_manifest() if hasattr(mod, "capability_manifest") else {}
        manifest_id = manifest.get("id") if isinstance(manifest, dict) else None

        print("PROOF_CAPABILITY_ID=", cap_id)
        print("PROOF_MANIFEST_ID=", manifest_id)

        canonical = "research_quality_analyzer"
        if cap_id != canonical:
            raise SystemExit("V65_51_ABORT=capability_id_not_canonical")
        if manifest_id != canonical:
            raise SystemExit("V65_51_ABORT=manifest_id_not_canonical")

        print("GENERATED_IDENTITY_CONSISTENCY=PASS")
finally:
    ce.ROOT, ce.STAGING = old_root, old_staging

print("SOURCE_RESTORED=FALSE")
print("V65_51_STABILITY_GATE=PASS")
print("V65_51_COMPLETE")
PY
