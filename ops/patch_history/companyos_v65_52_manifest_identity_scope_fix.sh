#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.52 MANIFEST IDENTITY SCOPE FIX ====="

python - <<'PY'
from pathlib import Path
import ast, shutil, time, py_compile, subprocess, sys, tempfile, importlib.util

ROOT = Path.home() / "companyos"
SRC = ROOT / "companyos/runtime/capability_expansion.py"
BACKUP = SRC.with_name(f"capability_expansion.py.v65_52_backup_{int(time.time())}")

text = SRC.read_text()
shutil.copy2(SRC, BACKUP)
print("BACKUP=", BACKUP)

tree = ast.parse(text)
stage = next(
    (n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "stage_plan"),
    None,
)
if stage is None:
    raise SystemExit("V65_52_ABORT=stage_plan_not_found")

# Find the V65.48 outer block: if module_content is not None:
outer = None
for n in ast.walk(stage):
    if isinstance(n, ast.If):
        try:
            expr = ast.unparse(n.test)
        except Exception:
            expr = ""
        if expr == "module_content is not None":
            # Prefer the block containing _cap_id_re.
            segment = ast.get_source_segment(text, n) or ""
            if "_cap_id_re" in segment:
                outer = n
                break

if outer is None:
    raise SystemExit("V65_52_ABORT=v65_48_outer_block_not_found")

lines = text.splitlines(keepends=True)
insert_idx = outer.end_lineno
func_indent = "    "
marker = "V65.52: canonicalize capability_manifest id on every generated module"

if marker not in text:
    block = [
        func_indent + "# " + marker + "\n",
        func_indent + "if module_content is not None:\n",
        func_indent + "    _manifest_id_re_v652 = re.compile(\n",
        func_indent + "        r\"(?s)(def\\s+capability_manifest\\s*\\([^)]*\\)\\s*:\\s*return\\s*\\{.*?['\\\"]id['\\\"]\\s*:\\s*)['\\\"][^'\\\"]*['\\\"]\"\n",
        func_indent + "    )\n",
        func_indent + "    module_content = _manifest_id_re_v652.sub(\n",
        func_indent + "        lambda m: m.group(1) + repr(canonical_id),\n",
        func_indent + "        module_content,\n",
        func_indent + "        count=1,\n",
        func_indent + "    )\n",
    ]
    lines[insert_idx:insert_idx] = block
    SRC.write_text("".join(lines))
    print("PATCH_STATUS=inserted_after_outer_identity_block")
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

# Show the exact patched area.
patched_lines = SRC.read_text().splitlines()
print("PATCH_CONTEXT_BEGIN")
for i, line in enumerate(patched_lines, 1):
    if "V65.48:" in line or "V65.51:" in line or "V65.52:" in line or "_manifest_id_re_v652" in line:
        lo=max(1,i-3); hi=min(len(patched_lines),i+10)
        for j in range(lo,hi+1):
            print(f"{j:04d}: {patched_lines[j-1]}")
        print("---")
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

# Direct sandbox proof of both public identities.
import companyos.runtime.capability_expansion as ce

plan = {
    "gap": {
        "id": "research_quality_analyzer",
        "title": "Research quality analyzer",
        "reason": "V65.52 identity scope proof",
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
            raise SystemExit("V65_52_ABORT=proof_stage_errors")

        module_rel, _ = ce.canonical_paths(plan["gap"]["id"])
        staged_module = Path(staged_root) / module_rel

        spec = importlib.util.spec_from_file_location("v65_52_probe", staged_module)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        cap_id = getattr(mod, "CAPABILITY_ID", None)
        manifest = mod.capability_manifest()
        manifest_id = manifest.get("id") if isinstance(manifest, dict) else None
        manifest_kind = manifest.get("kind") if isinstance(manifest, dict) else None

        print("PROOF_CAPABILITY_ID=", cap_id)
        print("PROOF_MANIFEST_ID=", manifest_id)
        print("PROOF_MANIFEST_KIND=", manifest_kind)

        canonical = "research_quality_analyzer"
        if cap_id != canonical:
            raise SystemExit("V65_52_ABORT=capability_id_not_canonical")
        if manifest_id != canonical:
            raise SystemExit("V65_52_ABORT=manifest_id_not_canonical")
        if manifest_kind != "analysis":
            raise SystemExit("V65_52_ABORT=manifest_metadata_lost")

        print("GENERATED_IDENTITY_CONSISTENCY=PASS")
        print("MANIFEST_METADATA_PRESERVED=PASS")
finally:
    ce.ROOT, ce.STAGING = old_root, old_staging

print("SOURCE_RESTORED=FALSE")
print("V65_52_STABILITY_GATE=PASS")
print("V65_52_COMPLETE")
PY
