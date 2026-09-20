#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"; export PYTHONPATH="$PWD"
echo "===== COMPANYOS V65.36 PROMOTE PATH CONTRACT FORENSICS ====="
python - <<'PY'
import tempfile, inspect, json
from pathlib import Path
import companyos.runtime.capability_expansion as ce

print("CANONICAL_PATHS_SOURCE_BEGIN")
print(inspect.getsource(ce.canonical_paths))
print("CANONICAL_PATHS_SOURCE_END")
print("PROMOTE_SOURCE_BEGIN")
print(inspect.getsource(ce.promote))
print("PROMOTE_SOURCE_END")

plan={"gap":{"id":"research_quality_analyzer","title":"Research quality analyzer","reason":"V65.36"},
"changes":[
{"path":"whatever.py","content":"CAPABILITY_ID='research_quality_analyzer'\ndef capability_manifest(): return {'id':'research_quality_analyzer'}\ndef evaluate(context): return {'ok':True}\n"},
{"path":"tests/generated/test_x.py","content":"import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n"}]}

old=(ce.ROOT,ce.STAGING,ce.PROMOTED)
with tempfile.TemporaryDirectory() as td:
    root=Path(td); ce.ROOT=root
    ce.STAGING=root/".companyos"/"capability_expansion"/"staging"
    ce.PROMOTED=root/".companyos"/"capability_expansion"/"promoted"
    try:
        _, staged, errors=ce.stage_plan(plan["gap"],plan)
        cid=ce.normalize_capability_id(plan["gap"]["id"])
        if errors: raise SystemExit("V65_36_ABORT=stage_errors")
        ok,_=ce.test_stage(Path(staged),cid)
        print("TEST_STAGE_OK=",ok)
        if not ok: raise SystemExit("V65_36_ABORT=test")
        module_path,test_path=ce.canonical_paths(cid)
        print("CANONICAL_RETURN_MODULE=",module_path)
        print("CANONICAL_RETURN_TEST=",test_path)
        print("MODULE_IS_ABSOLUTE=",Path(module_path).is_absolute())
        print("TEST_IS_ABSOLUTE=",Path(test_path).is_absolute())
        receipt=ce.promote(Path(staged),plan["gap"]["id"],cid)
        print("RECEIPT=",json.dumps(receipt,default=str))
        print("RECEIPT_MODULE=",receipt.get("module"))
        print("RECEIPT_TEST=",receipt.get("test"))
        for label,v in [("canonical_module",module_path),("canonical_test",test_path),
                        ("receipt_module",receipt.get("module")),("receipt_test",receipt.get("test"))]:
            if v:
                q=Path(v)
                print(label.upper()+"_EXISTS_DIRECT=",q.exists())
                print(label.upper()+"_EXISTS_UNDER_ROOT=",(root/q).exists() if not q.is_absolute() else "absolute")
        print("RECEIPT_FILE_EXISTS=",(ce.PROMOTED/cid/"receipt.json").exists())
        print("V65_36_FORENSICS=PASS")
    finally:
        ce.ROOT,ce.STAGING,ce.PROMOTED=old
print("V65_36_COMPLETE")
PY
