#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
export PYTHONPATH="$PWD"
echo "===== COMPANYOS V65.30 NORMALIZED-ID PIPELINE PROOF ====="
python - <<'PY'
import tempfile, traceback, json
from pathlib import Path
import companyos.runtime.capability_expansion as ce

plan={"gap":{"id":"research_quality_analyzer","title":"Research quality analyzer","reason":"V65.30 normalized-ID proof"},
"changes":[
{"path":"whatever.py","content":"CAPABILITY_ID='research_quality_analyzer'\ndef capability_manifest(): return {'id':'research_quality_analyzer'}\ndef evaluate(context): return {'ok':True}\n"},
{"path":"tests/generated/test_x.py","content":"import unittest\nclass T(unittest.TestCase):\n    def test_ok(self): self.assertTrue(True)\n"}]}

old_root,old_staging=ce.ROOT,ce.STAGING
with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    ce.ROOT=root
    ce.STAGING=root/".companyos"/"capability_expansion"/"staging"
    try:
        run_cid, staged_root, errors=ce.stage_plan(plan["gap"],plan)
        staged_root=Path(staged_root)
        normalized_id=ce.normalize_capability_id(plan["gap"]["id"])
        print("RUN_CID=",run_cid)
        print("NORMALIZED_ID=",normalized_id)
        print("STAGED_ROOT=",staged_root)
        print("STAGE_ERRORS=",errors)
        if errors: raise SystemExit("V65_30_ABORT=stage_errors")

        print("===== TEST_STAGE NORMALIZED ID =====")
        ok,steps=ce.test_stage(staged_root,normalized_id)
        print("TEST_STAGE_OK=",ok)
        print("TEST_STAGE_STEPS=",json.dumps(steps,indent=2,default=str))
        if not ok: raise SystemExit("V65_30_ABORT=test_stage_failed")

        print("===== PROMOTE NORMALIZED ID =====")
        receipt=ce.promote(staged_root,normalized_id)
        print("PROMOTE_RECEIPT=",json.dumps(receipt,indent=2,default=str))

        module_rel,test_rel=ce.canonical_paths(normalized_id)
        final_module=root/module_rel
        final_test=root/test_rel
        print("FINAL_MODULE=",final_module)
        print("FINAL_TEST=",final_test)
        print("FINAL_MODULE_EXISTS=",final_module.exists())
        print("FINAL_TEST_EXISTS=",final_test.exists())

        if not final_module.exists() or not final_test.exists():
            print("===== FINAL TREE =====")
            for f in sorted(x for x in root.rglob("*") if x.is_file()):
                print("FINAL_FILE=",f.relative_to(root))
            raise SystemExit("V65_30_ABORT=promotion_destination_mismatch")

        print("V65_30_NORMALIZED_ID_PIPELINE=PASS")
    except Exception:
        print("V65_30_EXCEPTION")
        traceback.print_exc()
        raise
    finally:
        ce.ROOT,ce.STAGING=old_root,old_staging
print("V65_30_COMPLETE")
PY
