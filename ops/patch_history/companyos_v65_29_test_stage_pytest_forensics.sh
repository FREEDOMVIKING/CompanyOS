#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
export PYTHONPATH="$PWD"
echo "===== COMPANYOS V65.29 TEST_STAGE PYTEST FORENSICS ====="

python - <<'PY'
import os, tempfile, subprocess, json, traceback
from pathlib import Path
import companyos.runtime.capability_expansion as ce

plan={"gap":{"id":"research_quality_analyzer","title":"Research quality analyzer","reason":"V65.29 pytest forensics"},
"changes":[
{"path":"whatever.py","content":"CAPABILITY_ID='research_quality_analyzer'\ndef capability_manifest(): return {'id':'research_quality_analyzer'}\ndef evaluate(context): return {'ok':True}\n"},
{"path":"tests/generated/test_x.py","content":"import unittest\nclass T(unittest.TestCase):\n    def test_ok(self): self.assertTrue(True)\n"}]}

old_root,old_staging=ce.ROOT,ce.STAGING
with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    ce.ROOT=root
    ce.STAGING=root/".companyos"/"capability_expansion"/"staging"
    try:
        cid, staged_root, errors=ce.stage_plan(plan["gap"],plan)
        staged_root=Path(staged_root)
        print("CID=",cid); print("STAGED_ROOT=",staged_root); print("STAGE_ERRORS=",errors)
        if errors: raise SystemExit("V65_29_ABORT=stage_errors")

        tests=sorted(p for p in staged_root.rglob("test_*.py"))
        mods=sorted(p for p in staged_root.rglob("*.py") if "tests" not in p.parts and p.name!="__init__.py")
        print("MODULES=",[str(x.relative_to(staged_root)) for x in mods])
        print("TESTS=",[str(x.relative_to(staged_root)) for x in tests])
        if not tests: raise SystemExit("V65_29_ABORT=no_test_discovered")

        print("===== BUILTIN TEST_STAGE =====")
        ok,steps=ce.test_stage(staged_root,cid)
        print("BUILTIN_OK=",ok)
        print("BUILTIN_STEPS_BEGIN")
        print(json.dumps(steps,indent=2,default=str))
        print("BUILTIN_STEPS_END")

        env=os.environ.copy()
        env["PYTHONPATH"]=str(staged_root)+os.pathsep+str(Path.cwd())

        print("===== DIRECT PYTEST =====")
        cp=subprocess.run(
            ["python","-m","pytest","-q",str(tests[0])],
            cwd=staged_root,env=env,text=True,capture_output=True,timeout=90
        )
        print("DIRECT_RETURN_CODE=",cp.returncode)
        print("DIRECT_STDOUT_BEGIN"); print(cp.stdout); print("DIRECT_STDOUT_END")
        print("DIRECT_STDERR_BEGIN"); print(cp.stderr); print("DIRECT_STDERR_END")

        print("===== DIRECT PY_COMPILE =====")
        for f in mods+tests:
            pc=subprocess.run(["python","-m","py_compile",str(f)],cwd=staged_root,env=env,text=True,capture_output=True,timeout=90)
            print("COMPILE_FILE=",f.relative_to(staged_root),"RC=",pc.returncode)
            if pc.stdout: print("COMPILE_STDOUT=",pc.stdout)
            if pc.stderr: print("COMPILE_STDERR=",pc.stderr)

        if cp.returncode==0 and not ok:
            print("V65_29_DIAGNOSIS=TEST_STAGE_CONTRACT_MISMATCH")
        elif cp.returncode!=0:
            print("V65_29_DIAGNOSIS=DIRECT_PYTEST_FAILURE")
        else:
            print("V65_29_DIAGNOSIS=TEST_STAGE_AND_DIRECT_PASS")

        print("V65_29_COMPLETE")
    except Exception:
        print("V65_29_EXCEPTION"); traceback.print_exc(); raise
    finally:
        ce.ROOT,ce.STAGING=old_root,old_staging
PY
