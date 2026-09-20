#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
export PYTHONPATH="$PWD"
echo "===== COMPANYOS V65.34 PROMOTED ROOT BINDING FIX ====="

python - <<'PY'
import tempfile, json
from pathlib import Path
import companyos.runtime.capability_expansion as ce

plan={"gap":{"id":"research_quality_analyzer","title":"Research quality analyzer","reason":"V65.34"},
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
        if errors: raise SystemExit("V65_34_ABORT=stage_errors")
        ok,steps=ce.test_stage(Path(staged_root),cid)
        print("TEST_STAGE_OK=",ok)
        if not ok: raise SystemExit("V65_34_ABORT=test_stage")
        receipt=ce.promote(Path(staged_root),plan["gap"]["id"],cid)
        promoted=ce.PROMOTED/cid
        print("PROMOTE_RECEIPT=",json.dumps(receipt,default=str))
        print("PROMOTED_ROOT=",promoted)
        print("PROMOTED_RECEIPT_EXISTS=",(promoted/"receipt.json").exists())
        print("PROMOTED_MODULE_EXISTS=",(promoted/"companies/extensions/generated/research_quality_analyzer.py").exists())
        print("PROMOTED_TEST_EXISTS=",(promoted/"tests/generated/test_research_quality_analyzer.py").exists())
        if not (promoted/"receipt.json").exists():
            raise SystemExit("V65_34_ABORT=receipt_missing")
        print("V65_34_SANDBOX_PROMOTION=PASS")
    finally:
        ce.ROOT,ce.STAGING,ce.PROMOTED=old_root,old_staging,old_promoted

print("LIVE_PROMOTED_ROOT=",ce.PROMOTED)
print("V65_34_COMPLETE")
PY
