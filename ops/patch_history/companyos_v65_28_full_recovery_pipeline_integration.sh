#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
export PYTHONPATH="$PWD"
echo "===== COMPANYOS V65.28 FULL RECOVERY PIPELINE ====="
python - <<'PY'
import tempfile, traceback, json, inspect
from pathlib import Path
import companyos.runtime.capability_expansion as ce

plan={"gap":{"id":"research_quality_analyzer","title":"Research quality analyzer","reason":"integration diagnostic"},
"changes":[
{"path":"whatever.py","content":"CAPABILITY_ID='research_quality_analyzer'\ndef capability_manifest(): return {'id':'research_quality_analyzer'}\ndef evaluate(context): return {'ok':True}\n"},
{"path":"tests/generated/test_x.py","content":"import unittest\nclass T(unittest.TestCase):\n    def test_ok(self): self.assertTrue(True)\n"}]}

print("STAGE_PLAN_SIGNATURE=",inspect.signature(ce.stage_plan))
print("TEST_STAGE_SIGNATURE=",inspect.signature(ce.test_stage))
print("PROMOTE_SIGNATURE=",inspect.signature(ce.promote))
old_root,old_staging=ce.ROOT,ce.STAGING

with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    ce.ROOT=root
    ce.STAGING=root/".companyos"/"capability_expansion"/"staging"
    try:
        cid,staged_root,errors=ce.stage_plan(plan["gap"],plan)
        print("CID=",cid); print("STAGED_ROOT=",staged_root); print("STAGE_ERRORS=",errors)
        if errors: raise SystemExit("V65_28_ABORT=stage_plan_errors")

        module_rel,test_rel=ce.canonical_paths(cid)
        module_path=Path(staged_root)/module_rel
        test_path=Path(staged_root)/test_rel
        print("MODULE_EXISTS=",module_path.exists()); print("TEST_EXISTS=",test_path.exists())
        if not module_path.exists() or not test_path.exists():
            raise SystemExit("V65_28_ABORT=staged_files_missing")

        print("===== TEST_STAGE =====")
        ok,steps=ce.test_stage(Path(staged_root),cid)
        print("TEST_STAGE_OK=",ok)
        print("TEST_STAGE_STEPS=",json.dumps(steps,default=str)[:12000])
        if not ok: raise SystemExit("V65_28_ABORT=test_stage_failed")

        print("===== PROMOTE =====")
        receipt=ce.promote(Path(staged_root),cid)
        print("PROMOTE_RECEIPT=",json.dumps(receipt,default=str)[:12000])
        print("FINAL_MODULE_EXISTS=",(root/module_rel).exists())
        print("FINAL_TEST_EXISTS=",(root/test_rel).exists())
        if not (root/module_rel).exists() or not (root/test_rel).exists():
            raise SystemExit("V65_28_ABORT=promotion_files_missing")
        print("V65_28_PIPELINE=PASS")
    except Exception:
        print("V65_28_EXCEPTION"); traceback.print_exc(); raise
    finally:
        ce.ROOT,ce.STAGING=old_root,old_staging
print("V65_28_COMPLETE")
PY
