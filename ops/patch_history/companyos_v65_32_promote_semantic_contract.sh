#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
export PYTHONPATH="$PWD"

echo "===== COMPANYOS V65.32 PROMOTE SEMANTIC CONTRACT ====="
python - <<'PY'
import inspect, tempfile, json, traceback
from pathlib import Path
import companyos.runtime.capability_expansion as ce

sig=inspect.signature(ce.promote)
print("PROMOTE_SIGNATURE=",sig)
print("PROMOTE_SOURCE_BEGIN")
print(inspect.getsource(ce.promote))
print("PROMOTE_SOURCE_END")

plan={"gap":{"id":"research_quality_analyzer","title":"Research quality analyzer","reason":"V65.32"},
"changes":[
{"path":"whatever.py","content":"CAPABILITY_ID='research_quality_analyzer'\ndef capability_manifest(): return {'id':'research_quality_analyzer'}\ndef evaluate(context): return {'ok':True}\n"},
{"path":"tests/generated/test_x.py","content":"import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n"}]}

old_root,old_staging=ce.ROOT,ce.STAGING
with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    ce.ROOT=root
    ce.STAGING=root/".companyos"/"capability_expansion"/"staging"
    try:
        run_cid, staged_root, errors=ce.stage_plan(plan["gap"],plan)
        staged_root=Path(staged_root)
        cid=ce.normalize_capability_id(plan["gap"]["id"])
        print("CID=",cid)
        print("STAGED_ROOT=",staged_root)
        print("STAGE_ERRORS=",errors)
        if errors: raise SystemExit("V65_32_ABORT=stage_errors")
        ok,steps=ce.test_stage(staged_root,cid)
        print("TEST_STAGE_OK=",ok)
        if not ok: raise SystemExit("V65_32_ABORT=test_stage_failed")

        # Current live contract observed: promote(root, gap_id, cid)
        params=list(sig.parameters)
        print("PROMOTE_PARAMS=",params)
        if params == ["root","gap_id","cid"]:
            args=(staged_root, plan["gap"]["id"], cid)
        else:
            raise SystemExit("V65_32_ABORT=unexpected_promote_signature:"+str(sig))

        print("PROMOTE_ARGS=",tuple(map(str,args)))
        receipt=ce.promote(*args)
        print("PROMOTE_RECEIPT=",json.dumps(receipt,indent=2,default=str))

        module_rel,test_rel=ce.canonical_paths(cid)
        promoted_root=ce.PROMOTED / cid
        print("PROMOTED_ROOT=",promoted_root)
        print("PROMOTED_RECEIPT_EXISTS=",(promoted_root/"receipt.json").exists())
        print("SOURCE_STILL_EXISTS=",staged_root.exists())
        print("V65_32_PROMOTE_CALL=PASS")
    except Exception:
        traceback.print_exc()
        raise
    finally:
        ce.ROOT,ce.STAGING=old_root,old_staging
print("V65_32_COMPLETE")
PY
