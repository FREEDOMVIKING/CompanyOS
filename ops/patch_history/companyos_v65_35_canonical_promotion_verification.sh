#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
export PYTHONPATH="$PWD"
echo "===== COMPANYOS V65.35 CANONICAL PROMOTION VERIFICATION ====="

python - <<'PY'
import tempfile, json
from pathlib import Path
import companyos.runtime.capability_expansion as ce

plan={"gap":{"id":"research_quality_analyzer","title":"Research quality analyzer","reason":"V65.35"},
"changes":[
{"path":"whatever.py","content":"CAPABILITY_ID='research_quality_analyzer'\ndef capability_manifest(): return {'id':'research_quality_analyzer'}\ndef evaluate(context): return {'ok':True}\n"},
{"path":"tests/generated/test_x.py","content":"import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n"}]}

old_root,old_staging,old_promoted=ce.ROOT,ce.STAGING,ce.PROMOTED
with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    ce.ROOT=root
    ce.STAGING=root/".companyos"/"capability_expansion"/"staging"
    ce.PROMOTED=root/".companyos"/"capability_expansion"/"promoted"
    try:
        run_cid, staged_root, errors=ce.stage_plan(plan["gap"],plan)
        cid=ce.normalize_capability_id(plan["gap"]["id"])
        print("NORMALIZED_ID=",cid)
        print("STAGE_ERRORS=",errors)
        if errors: raise SystemExit("V65_35_ABORT=stage_errors")

        ok,steps=ce.test_stage(Path(staged_root),cid)
        print("TEST_STAGE_OK=",ok)
        if not ok: raise SystemExit("V65_35_ABORT=test_stage")

        module_rel,test_rel=ce.canonical_paths(cid)
        canonical_module=root/module_rel
        canonical_test=root/test_rel
        receipt=ce.promote(Path(staged_root),plan["gap"]["id"],cid)
        receipt_path=ce.PROMOTED/cid/"receipt.json"

        print("PROMOTE_RECEIPT=",json.dumps(receipt,default=str))
        print("CANONICAL_MODULE=",canonical_module)
        print("CANONICAL_TEST=",canonical_test)
        print("CANONICAL_MODULE_EXISTS=",canonical_module.exists())
        print("CANONICAL_TEST_EXISTS=",canonical_test.exists())
        print("PROMOTED_RECEIPT_EXISTS=",receipt_path.exists())

        if not canonical_module.exists(): raise SystemExit("V65_35_ABORT=canonical_module_missing")
        if not canonical_test.exists(): raise SystemExit("V65_35_ABORT=canonical_test_missing")
        if not receipt_path.exists(): raise SystemExit("V65_35_ABORT=receipt_missing")

        import py_compile, subprocess, os
        py_compile.compile(str(canonical_module),doraise=True)
        env=os.environ.copy()
        env["PYTHONPATH"]=str(root)+os.pathsep+env.get("PYTHONPATH","")
        cp=subprocess.run(["python","-m","pytest","-q",str(canonical_test)],
                          cwd=root,env=env,text=True,capture_output=True,timeout=90)
        print("CANONICAL_TEST_RC=",cp.returncode)
        if cp.stdout: print(cp.stdout)
        if cp.stderr: print(cp.stderr)
        if cp.returncode != 0: raise SystemExit("V65_35_ABORT=canonical_test_failed")

        print("V65_35_CANONICAL_PROMOTION=PASS")
    finally:
        ce.ROOT,ce.STAGING,ce.PROMOTED=old_root,old_staging,old_promoted

print("V65_35_COMPLETE")
PY
