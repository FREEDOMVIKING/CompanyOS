#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
export PYTHONPATH="$PWD"
echo "===== COMPANYOS V65.33 RECOVERY PIPELINE INTEGRATION ====="

python - <<'PY'
from pathlib import Path
import ast, inspect, py_compile, shutil, time
p=Path("companyos/runtime/capability_expansion.py")
src=p.read_text()
backup=p.with_name(p.name+f".v65_33_backup_{time.strftime('%Y%m%d_%H%M%S')}")
shutil.copy2(p,backup)
print("BACKUP=",backup)

tree=ast.parse(src)
fn={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
for name in ("stage_plan","test_stage","promote","canonical_paths","normalize_capability_id"):
    if name not in fn:
        raise SystemExit("V65_33_ABORT=missing_function:"+name)

print("STAGE_PLAN_SIGNATURE=",inspect.signature(__import__("companyos.runtime.capability_expansion",fromlist=[""]).stage_plan))
print("PROMOTE_SIGNATURE=",inspect.signature(__import__("companyos.runtime.capability_expansion",fromlist=[""]).promote))
py_compile.compile(str(p),doraise=True)
print("SOURCE_COMPILE=PASS")
print("V65_33_PREFLIGHT=PASS")
PY

python - <<'PY'
import tempfile, os, subprocess
from pathlib import Path
import companyos.runtime.capability_expansion as ce

plan={"gap":{"id":"research_quality_analyzer","title":"Research quality analyzer","reason":"integration-proof"},
"changes":[
{"path":"whatever.py","content":"CAPABILITY_ID='research_quality_analyzer'\ndef capability_manifest(): return {'id':'research_quality_analyzer'}\ndef evaluate(context): return {'ok':True}\n"},
{"path":"tests/generated/test_x.py","content":"import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n"}]}

old_root,old_staging=ce.ROOT,ce.STAGING
with tempfile.TemporaryDirectory() as td:
    root=Path(td); ce.ROOT=root; ce.STAGING=root/".companyos"/"capability_expansion"/"staging"
    try:
        run_cid, staged_root, errors=ce.stage_plan(plan["gap"],plan)
        cid=ce.normalize_capability_id(plan["gap"]["id"])
        print("NORMALIZED_ID=",cid)
        print("STAGE_ERRORS=",errors)
        if errors: raise SystemExit("V65_33_ABORT=stage")
        ok,steps=ce.test_stage(Path(staged_root),cid)
        print("TEST_STAGE_OK=",ok)
        if not ok: raise SystemExit("V65_33_ABORT=test")
        receipt=ce.promote(Path(staged_root),plan["gap"]["id"],cid)
        print("PROMOTE_OK=",bool(receipt))
        promoted=ce.PROMOTED/cid
        print("PROMOTED_RECEIPT_EXISTS=",(promoted/"receipt.json").exists())
        if not (promoted/"receipt.json").exists(): raise SystemExit("V65_33_ABORT=receipt")
        print("V65_33_END_TO_END=PASS")
    finally:
        ce.ROOT,ce.STAGING=old_root,old_staging
PY

echo "===== TARGETED REGRESSION ====="
python -m pytest -q tests/test_capability_expansion_test_recovery_v5.py || {
  echo "V65_33_NOTE=legacy recovery fixture still disagrees with normalized-ID contract"
  exit 2
}
echo "V65_33_REGRESSION=PASS"
echo "V65_33_COMPLETE"
