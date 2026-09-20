#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"; export PYTHONPATH="$PWD"
echo "===== COMPANYOS V65.38 STAGE_TEST CONTRACT FORENSICS ====="
python - <<'PY'
import inspect, tempfile, json
from pathlib import Path
import companyos.runtime.capability_expansion as ce

print("TEST_STAGE_SIGNATURE=", inspect.signature(ce.test_stage))
print("TEST_STAGE_SOURCE_BEGIN")
print(inspect.getsource(ce.test_stage))
print("TEST_STAGE_SOURCE_END")

plan={"gap":{"id":"research_quality_analyzer","title":"Research quality analyzer","reason":"V65.38"},
"changes":[
{"path":"whatever.py","content":"CAPABILITY_ID='research_quality_analyzer'\ndef capability_manifest(): return {'id':'research_quality_analyzer'}\ndef evaluate(context): return {'ok':True}\n"},
{"path":"tests/generated/test_x.py","content":"import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n"}]}

old=(ce.ROOT,ce.STAGING,ce.PROMOTED)
with tempfile.TemporaryDirectory() as td:
    root=Path(td); ce.ROOT=root
    ce.STAGING=root/".companyos"/"capability_expansion"/"staging"
    ce.PROMOTED=root/".companyos"/"capability_expansion"/"promoted"
    try:
        cid, staged, errors=ce.stage_plan(plan["gap"],plan)
        staged=Path(staged)
        print("CID=",cid)
        print("STAGED_ROOT=",staged)
        print("STAGE_ERRORS=",errors)
        print("STAGED_TREE_BEGIN")
        for f in sorted(staged.rglob("*")):
            if f.is_file():
                print("FILE=",f.relative_to(staged))
        print("STAGED_TREE_END")
        try:
            result=ce.test_stage(staged,cid)
            print("RAW_TEST_STAGE_RESULT=",repr(result))
            if isinstance(result,tuple) and len(result)>=2:
                print("TEST_STAGE_OK=",repr(result[0]))
                print("TEST_STAGE_STEPS=",json.dumps(result[1],indent=2,default=str))
        except Exception as exc:
            print("TEST_STAGE_EXCEPTION=",type(exc).__name__,repr(exc))
        print("V65_38_FORENSICS=PASS")
    finally:
        ce.ROOT,ce.STAGING,ce.PROMOTED=old
PY
echo "V65_38_COMPLETE"
