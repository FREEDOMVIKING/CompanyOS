#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.40 STAGE TEST CONTRACT DIAGNOSTICS ====="

python - <<'PY'
import inspect, json, tempfile, traceback
from pathlib import Path
import companyos.runtime.capability_expansion as ce

print("STAGE_PLAN_SIGNATURE=", inspect.signature(ce.stage_plan))
print("TEST_STAGE_SIGNATURE=", inspect.signature(ce.test_stage))

plan = {
    "gap": {
        "id": "research_quality_analyzer",
        "title": "Research quality analyzer",
        "reason": "diagnostic",
    },
    "changes": [
        {
            "path": "whatever.py",
            "content": (
                'CAPABILITY_ID="research_quality_analyzer"\n'
                'def capability_manifest(): return {"id":"research_quality_analyzer"}\n'
                'def evaluate(context): return {"ok":True}\n'
            ),
        },
        {
            "path": "tests/generated/test_x.py",
            "content": (
                "import unittest\n"
                "class T(unittest.TestCase):\n"
                "    def test_ok(self): self.assertTrue(True)\n"
            ),
        },
    ],
}

old_root = ce.ROOT
old_staging = ce.STAGING
try:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        ce.ROOT = root
        ce.STAGING = root / ".companyos" / "capability_expansion" / "staging"

        cid, staged_root, errors = ce.stage_plan(plan["gap"], plan)
        print("CID=", cid)
        print("STAGED_ROOT=", staged_root)
        print("STAGE_ERRORS=", errors)

        sr = Path(staged_root)
        print("FILES_BEGIN")
        for f in sorted(sr.rglob("*")):
            if f.is_file():
                print("FILE=", f.relative_to(sr))
        print("FILES_END")

        result = ce.test_stage(plan["gap"], plan)
        print("TEST_STAGE_RETURN_TYPE=", type(result).__name__)
        print("TEST_STAGE_RETURN_REPR=", repr(result))

        # Show the implementation only around test_stage so we diagnose
        # the real return contract rather than guessing.
        print("TEST_STAGE_SOURCE_BEGIN")
        print(inspect.getsource(ce.test_stage))
        print("TEST_STAGE_SOURCE_END")

        # If test_stage returned structured data, expose it cleanly.
        if isinstance(result, dict):
            print("TEST_STAGE_JSON=", json.dumps(result, indent=2, default=str))
        elif isinstance(result, (tuple, list)):
            for i, item in enumerate(result):
                print(f"TEST_STAGE_ITEM_{i}=", repr(item))

except Exception:
    print("V65_40_EXCEPTION_BEGIN")
    traceback.print_exc()
    print("V65_40_EXCEPTION_END")
    raise
finally:
    ce.ROOT = old_root
    ce.STAGING = old_staging

print("V65_40_DIAGNOSTICS_COMPLETE")
PY
