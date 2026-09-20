#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"; export PYTHONPATH="$PWD"
echo "===== COMPANYOS V65.37 CANONICAL PROMOTION END-TO-END ====="
python - <<'PY'
import tempfile, os, subprocess, json
from pathlib import Path
import companyos.runtime.capability_expansion as ce

plan={"gap":{"id":"research_quality_analyzer","title":"Research quality analyzer","reason":"V65.37"},
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
        print("CID=",cid); print("STAGE_ERRORS=",errors)
        if errors: raise SystemExit("V65_37_ABORT=stage_errors")

        ok, steps=ce.test_stage(Path(staged),cid)
        print("TEST_STAGE_OK=",ok)
        if not ok:
            print("TEST_STAGE_STEPS=",json.dumps(steps,default=str))
            raise SystemExit("V65_37_ABORT=stage_test")

        receipt=ce.promote(Path(staged),plan["gap"]["id"],cid)
        print("RECEIPT=",json.dumps(receipt,default=str))

        module_rel,test_rel=ce.canonical_paths(cid)
        module_path=root/Path(module_rel)
        test_path=root/Path(test_rel)
        print("MODULE_PATH=",module_path)
        print("TEST_PATH=",test_path)
        print("MODULE_EXISTS=",module_path.exists())
        print("TEST_EXISTS=",test_path.exists())
        print("RECEIPT_EXISTS=",(ce.PROMOTED/cid/"receipt.json").exists())
        if not module_path.exists() or not test_path.exists():
            raise SystemExit("V65_37_ABORT=canonical_files_missing")

        env=os.environ.copy()
        env["PYTHONPATH"]=str(root)+os.pathsep+env.get("PYTHONPATH","")
        cmds=[
          ["python","-m","py_compile",str(module_path),str(test_path)],
          ["python","-m","pytest","-q",str(test_path)],
        ]
        for cmd in cmds:
            print("COMMAND="," ".join(cmd))
            cp=subprocess.run(cmd,cwd=root,env=env,text=True,capture_output=True,timeout=90)
            print("RETURN_CODE=",cp.returncode)
            if cp.stdout: print("STDOUT:\n"+cp.stdout)
            if cp.stderr: print("STDERR:\n"+cp.stderr)
            if cp.returncode: raise SystemExit("V65_37_ABORT=promoted_validation_failed")

        print("V65_37_CANONICAL_PROMOTION=PASS")
    finally:
        ce.ROOT,ce.STAGING,ce.PROMOTED=old
print("V65_37_COMPLETE")
PY
