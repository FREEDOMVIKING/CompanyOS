#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
export PYTHONPATH="$PWD"
echo "===== COMPANYOS V65.28B ACTUAL STAGING TREE PIPELINE ====="
python - <<'PY'
import tempfile, traceback, json, inspect
from pathlib import Path
import companyos.runtime.capability_expansion as ce

plan={"gap":{"id":"research_quality_analyzer","title":"Research quality analyzer","reason":"V65.28B integration diagnostic"},
"changes":[
{"path":"whatever.py","content":"CAPABILITY_ID='research_quality_analyzer'\ndef capability_manifest(): return {'id':'research_quality_analyzer'}\ndef evaluate(context): return {'ok':True}\n"},
{"path":"tests/generated/test_x.py","content":"import unittest\nclass T(unittest.TestCase):\n    def test_ok(self): self.assertTrue(True)\n"}]}

old_root,old_staging=ce.ROOT,ce.STAGING
with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    ce.ROOT=root
    ce.STAGING=root/".companyos"/"capability_expansion"/"staging"
    try:
        cid, staged_root, errors = ce.stage_plan(plan["gap"], plan)
        staged_root=Path(staged_root)
        print("CID=",cid)
        print("STAGED_ROOT=",staged_root)
        print("STAGE_ERRORS=",errors)
        if errors: raise SystemExit("V65_28B_ABORT=stage_plan_errors")

        files=sorted(p for p in staged_root.rglob("*") if p.is_file())
        print("STAGED_FILE_COUNT=",len(files))
        for f in files:
            print("STAGED_FILE=",f.relative_to(staged_root))

        pyfiles=[f for f in files if f.suffix==".py"]
        modules=[f for f in pyfiles if "tests" not in f.parts and f.name!="__init__.py"]
        tests=[f for f in pyfiles if "tests" in f.parts and f.name.startswith("test_")]
        print("DISCOVERED_MODULES=",[str(x.relative_to(staged_root)) for x in modules])
        print("DISCOVERED_TESTS=",[str(x.relative_to(staged_root)) for x in tests])
        if not modules or not tests:
            raise SystemExit("V65_28B_ABORT=actual_staged_files_missing")

        print("===== TEST_STAGE =====")
        ok,steps=ce.test_stage(staged_root,cid)
        print("TEST_STAGE_OK=",ok)
        print("TEST_STAGE_STEPS=",json.dumps(steps,default=str)[:12000])
        if not ok: raise SystemExit("V65_28B_ABORT=test_stage_failed")

        print("===== PROMOTE =====")
        receipt=ce.promote(staged_root,cid)
        print("PROMOTE_RECEIPT=",json.dumps(receipt,default=str)[:12000])

        expected_module=root/"companyos"/"extensions"/"generated"/"research_quality_analyzer.py"
        expected_test=root/"tests"/"generated"/"test_research_quality_analyzer.py"
        print("FINAL_MODULE_EXISTS=",expected_module.exists())
        print("FINAL_TEST_EXISTS=",expected_test.exists())
        if not expected_module.exists() or not expected_test.exists():
            print("ROOT_TREE_AFTER_PROMOTE=")
            for f in sorted(p for p in root.rglob("*") if p.is_file()):
                print("FINAL_FILE=",f.relative_to(root))
            raise SystemExit("V65_28B_ABORT=promotion_destination_mismatch")

        print("V65_28B_PIPELINE=PASS")
    except Exception:
        print("V65_28B_EXCEPTION")
        traceback.print_exc()
        raise
    finally:
        ce.ROOT,ce.STAGING=old_root,old_staging
print("V65_28B_COMPLETE")
PY
