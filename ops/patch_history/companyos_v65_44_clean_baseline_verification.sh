#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.44 CLEAN BASELINE VERIFICATION ====="

python -m py_compile companyos/runtime/capability_expansion.py
echo "SOURCE_COMPILE=PASS"

python - <<'PY'
import inspect
import companyos.runtime.capability_expansion as ce
print("STAGE_PLAN_SIGNATURE=", inspect.signature(ce.stage_plan))
print("TEST_STAGE_SIGNATURE=", inspect.signature(ce.test_stage))
print("PROMOTE_SIGNATURE=", inspect.signature(ce.promote))
print("TEST_STAGE_SOURCE_BEGIN")
print(inspect.getsource(ce.test_stage))
print("TEST_STAGE_SOURCE_END")
PY

echo "===== TARGETED RECOVERY TEST ====="
python -m pytest -q tests/test_capability_expansion_test_recovery_v5.py
echo "TARGETED_RECOVERY_TEST=PASS"

echo "===== SANDBOX END-TO-END ====="
python - <<'PY'
import tempfile, os, subprocess, json
from pathlib import Path
import companyos.runtime.capability_expansion as ce

plan={
  "gap":{"id":"research_quality_analyzer","title":"Research quality analyzer","reason":"V65.44"},
  "changes":[
    {"path":"whatever.py","content":
      "CAPABILITY_ID='research_quality_analyzer'\n"
      "def capability_manifest(): return {'id':'research_quality_analyzer'}\n"
      "def evaluate(context): return {'ok':True}\n"},
    {"path":"tests/generated/test_x.py","content":
      "import unittest\n"
      "class T(unittest.TestCase):\n"
      "    def test_ok(self): self.assertTrue(True)\n"}
  ]
}

old_root, old_staging, old_promoted = ce.ROOT, ce.STAGING, ce.PROMOTED
with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    ce.ROOT=root
    ce.STAGING=root/".companyos"/"capability_expansion"/"staging"
    ce.PROMOTED=root/".companyos"/"capability_expansion"/"promoted"
    try:
        run_cid, staged_root, errors = ce.stage_plan(plan["gap"], plan)
        normalized_id = ce.normalize_capability_id(plan["gap"]["id"])
        print("RUN_CID=", run_cid)
        print("NORMALIZED_ID=", normalized_id)
        print("STAGED_ROOT=", staged_root)
        print("STAGE_ERRORS=", errors)
        if errors:
            raise SystemExit("V65_44_ABORT=stage_errors")

        ok, steps = ce.test_stage(Path(staged_root), normalized_id)
        print("TEST_STAGE_OK=", ok)
        print("TEST_STAGE_STEPS=", json.dumps(steps, default=str))
        if not ok:
            raise SystemExit("V65_44_ABORT=test_stage_failed")

        receipt = ce.promote(Path(staged_root), plan["gap"]["id"], normalized_id)
        print("PROMOTE_RECEIPT=", json.dumps(receipt, default=str))

        module_rel, test_rel = ce.canonical_paths(normalized_id)
        module_path = root / module_rel
        test_path = root / test_rel
        receipt_path = ce.PROMOTED / normalized_id / "receipt.json"

        print("MODULE_EXISTS=", module_path.exists())
        print("TEST_EXISTS=", test_path.exists())
        print("RECEIPT_EXISTS=", receipt_path.exists())

        if not (module_path.exists() and test_path.exists() and receipt_path.exists()):
            raise SystemExit("V65_44_ABORT=promotion_verification_failed")

        env=os.environ.copy()
        env["PYTHONPATH"]=str(root)+os.pathsep+env.get("PYTHONPATH","")
        cp=subprocess.run(
            ["python","-m","pytest","-q",str(test_path)],
            cwd=root,env=env,text=True,capture_output=True,timeout=90
        )
        print("PROMOTED_TEST_RC=", cp.returncode)
        if cp.stdout: print(cp.stdout)
        if cp.stderr: print(cp.stderr)
        if cp.returncode != 0:
            raise SystemExit("V65_44_ABORT=promoted_test_failed")

        print("V65_44_END_TO_END=PASS")
    finally:
        ce.ROOT, ce.STAGING, ce.PROMOTED = old_root, old_staging, old_promoted
PY

echo "V65_44_COMPLETE"
