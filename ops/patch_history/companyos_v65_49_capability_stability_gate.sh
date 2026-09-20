#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.49 CAPABILITY STABILITY GATE ====="
echo "SOURCE_WRITES=0"

python - <<'PY'
from pathlib import Path
import json, py_compile, subprocess, sys, time, inspect

ROOT = Path.home() / "companyos"
SRC = ROOT / "companyos/runtime/capability_expansion.py"
REPORT_DIR = Path.home() / ".companyos_runtime/reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

report = {
    "version": "V65.49",
    "timestamp": int(time.time()),
    "source_writes": 0,
    "checks": [],
}

def record(name, ok, detail=""):
    report["checks"].append({"name": name, "ok": bool(ok), "detail": detail})
    print(f"{name}={'PASS' if ok else 'FAIL'}")
    if detail:
        print(detail)

try:
    py_compile.compile(str(SRC), doraise=True)
    record("SOURCE_COMPILE", True)
except Exception as e:
    record("SOURCE_COMPILE", False, repr(e))
    raise SystemExit(1)

try:
    import companyos.runtime.capability_expansion as ce
    record("SOURCE_IMPORT", True)
    print("STAGE_PLAN_SIGNATURE=", inspect.signature(ce.stage_plan))
    print("TEST_STAGE_SIGNATURE=", inspect.signature(ce.test_stage))
    print("PROMOTE_SIGNATURE=", inspect.signature(ce.promote))
except Exception as e:
    record("SOURCE_IMPORT", False, repr(e))
    raise SystemExit(1)

# Only canonical test files in tests/, never backups or copied trees.
tests = sorted(
    p for p in (ROOT / "tests").glob("test_capability_expansion*.py")
    if ".bak" not in p.name and "backup" not in p.name
)
print("TEST_FILES=", [p.name for p in tests])

if not tests:
    record("TEST_DISCOVERY", False, "No canonical capability-expansion tests found")
    raise SystemExit(1)
record("TEST_DISCOVERY", True, f"{len(tests)} files")

overall = True
for test in tests:
    cmd = [sys.executable, "-m", "pytest", "-q", str(test)]
    cp = subprocess.run(
        cmd, cwd=str(ROOT), text=True, capture_output=True, timeout=180
    )
    ok = cp.returncode == 0
    overall = overall and ok
    print(f"\n===== {test.name} =====")
    print("RETURN_CODE=", cp.returncode)
    if cp.stdout:
        print(cp.stdout[-12000:])
    if cp.stderr:
        print(cp.stderr[-5000:])
    record(f"PYTEST::{test.name}", ok)

# Prove the V65.48 behavior itself: a placeholder generated CAPABILITY_ID
# must be canonicalized when stage_plan writes the staged module.
import tempfile
from pathlib import Path
import companyos.runtime.capability_expansion as ce

plan = {
    "gap": {
        "id": "research_quality_analyzer",
        "title": "Research quality analyzer",
        "reason": "V65.49 stability proof",
    },
    "changes": [
        {
            "path": "whatever.py",
            "content": (
                "CAPABILITY_ID='placeholder_id'\n"
                "def capability_manifest(): return {'id':'placeholder_id'}\n"
                "def evaluate(context): return {'ok':True}\n"
            ),
        },
        {
            "path": "tests/generated/test_x.py",
            "content": (
                "import unittest\n"
                "from companies.extensions.generated.research_quality_analyzer "
                "import CAPABILITY_ID\n"
                "class T(unittest.TestCase):\n"
                "    def test_id(self): "
                "self.assertEqual(CAPABILITY_ID,'research_quality_analyzer')\n"
            ),
        },
    ],
}

old_root, old_staging = ce.ROOT, ce.STAGING
try:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        ce.ROOT = root
        ce.STAGING = root / ".companyos" / "capability_expansion" / "staging"
        cid, staged_root, errors = ce.stage_plan(plan["gap"], plan)
        print("PROOF_CID=", cid)
        print("PROOF_STAGE_ERRORS=", errors)
        if errors:
            record("CANONICAL_ID_STAGE_PROOF", False, repr(errors))
            overall = False
        else:
            module_rel, _ = ce.canonical_paths(plan["gap"]["id"])
            staged_module = Path(staged_root) / module_rel
            content = staged_module.read_text()
            canonical_ok = "CAPABILITY_ID='research_quality_analyzer'" in content or \
                           'CAPABILITY_ID="research_quality_analyzer"' in content
            record("CANONICAL_ID_STAGE_PROOF", canonical_ok)
            overall = overall and canonical_ok
finally:
    ce.ROOT, ce.STAGING = old_root, old_staging

report["overall_pass"] = overall
rp = REPORT_DIR / f"v65_49_capability_stability_{report['timestamp']}.json"
rp.write_text(json.dumps(report, indent=2))
print("\nREPORT=", rp)

if not overall:
    print("V65_49_STABILITY_GATE=FAIL")
    raise SystemExit(1)

print("V65_49_STABILITY_GATE=PASS")
print("V65_49_COMPLETE")
PY
