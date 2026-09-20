#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
export GIT_PAGER=cat
export PAGER=cat

echo "===== COMPANYOS V65.58 INTEGRITY GUARD EVALUATE COMPAT FIX ====="

python - <<'PY'
from pathlib import Path
import ast, shutil, time, py_compile, subprocess, sys, importlib

ROOT = Path.home() / "companyos"
SRC = ROOT / "companyos/resilienceops/data_integrity.py"
TEST = ROOT / "tests/test_phase1501_12000.py"
BACKUP = SRC.with_name(f"data_integrity.py.v65_58_backup_{int(time.time())}")

text = SRC.read_text()
shutil.copy2(SRC, BACKUP)
print("BACKUP=", BACKUP)

tree = ast.parse(text)
klass = next(
    (n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "DataIntegrityGuard"),
    None,
)
if klass is None:
    raise SystemExit("V65_58_ABORT=DataIntegrityGuard_not_found")

marker = "V65.58 legacy evaluate contract"
lines = text.splitlines(keepends=True)

if marker not in text:
    insert_at = klass.end_lineno
    method = [
        "\n",
        "    @staticmethod\n",
        "    def evaluate(items):\n",
        "        # V65.58 legacy evaluate contract: phase/runtime callers pass\n",
        "        # integrity-check rows shaped like {'name': ..., 'passed': bool}.\n",
        "        rows = list(items or [])\n",
        "        if all(isinstance(item, dict) and 'passed' in item for item in rows):\n",
        "            failed = [item for item in rows if not bool(item.get('passed'))]\n",
        "            issues = [\n",
        "                {\n",
        "                    'id': str(item.get('name') or f'check-{idx + 1}'),\n",
        "                    'code': 'check_failed',\n",
        "                    'message': 'integrity check failed',\n",
        "                }\n",
        "                for idx, item in enumerate(failed)\n",
        "            ]\n",
        "            ok = not failed\n",
        "            return {\n",
        "                'integrity_ok': ok,\n",
        "                'valid': ok,\n",
        "                'items': len(rows),\n",
        "                'issue_count': len(issues),\n",
        "                'issues': issues,\n",
        "            }\n",
        "\n",
        "        # Current work-item contract remains unchanged for non-legacy rows.\n",
        "        report = dict(validate_work_items(rows))\n",
        "        report['integrity_ok'] = bool(report.get('valid'))\n",
        "        return report\n",
    ]
    lines[insert_at:insert_at] = method
    SRC.write_text("".join(lines))
    print("PATCH_STATUS=inserted")
else:
    print("PATCH_STATUS=already_present")

try:
    py_compile.compile(str(SRC), doraise=True)
    print("PY_COMPILE=PASS")
except Exception:
    shutil.copy2(BACKUP, SRC)
    print("PY_COMPILE=FAIL")
    print("SOURCE_RESTORED=TRUE")
    raise

# Reload and prove both evaluate modes.
import companyos.resilienceops.data_integrity as di
di = importlib.reload(di)

legacy_ok = di.DataIntegrityGuard().evaluate([{"name":"x","passed":True}])
legacy_bad = di.DataIntegrityGuard().evaluate([
    {"name":"x","passed":True},
    {"name":"y","passed":False},
])
work_item = di.DataIntegrityGuard().evaluate([
    {"id":"a","title":"A","status":"ready"}
])

print("LEGACY_OK=", legacy_ok)
print("LEGACY_BAD=", legacy_bad)
print("WORK_ITEM_RESULT=", work_item)

if legacy_ok.get("integrity_ok") is not True:
    shutil.copy2(BACKUP, SRC)
    raise SystemExit("V65_58_ABORT=legacy_true_contract_failed")
if legacy_bad.get("integrity_ok") is not False:
    shutil.copy2(BACKUP, SRC)
    raise SystemExit("V65_58_ABORT=legacy_false_contract_failed")
if "summary" not in work_item or "fingerprint" not in work_item:
    shutil.copy2(BACKUP, SRC)
    raise SystemExit("V65_58_ABORT=current_validation_contract_changed")

print("DIRECT_COMPAT_PROOF=PASS")

def run(label, args, timeout=180):
    cp = subprocess.run(args, cwd=str(ROOT), text=True, capture_output=True, timeout=timeout)
    print(f"\n===== {label} =====")
    print("RETURN_CODE=", cp.returncode)
    if cp.stdout:
        print(cp.stdout[-16000:])
    if cp.stderr:
        print(cp.stderr[-6000:])
    return cp.returncode

# Run the whole phase test file; avoids node-id/path quirks from V65.57.
if TEST.exists():
    rc = run(
        "PHASE1501_12000_TEST_FILE",
        [sys.executable, "-m", "pytest", "-q", str(TEST)],
        120,
    )
    if rc != 0:
        shutil.copy2(BACKUP, SRC)
        py_compile.compile(str(SRC), doraise=True)
        print("PHASE_TEST=FAIL")
        print("SOURCE_RESTORED=TRUE")
        raise SystemExit(rc)
    print("PHASE_TEST=PASS")
else:
    print("PHASE_TEST_FILE_MISSING=TRUE")

# Continue immediately to the next real full-suite failure.
OUT = Path.home() / ".companyos_runtime/tmp" / f"v65_58_fullsuite_{int(time.time())}.out"
OUT.parent.mkdir(parents=True, exist_ok=True)

with OUT.open("w") as fh:
    cp = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-x"],
        cwd=str(ROOT),
        text=True,
        stdout=fh,
        stderr=subprocess.STDOUT,
        timeout=900,
    )

print("FULL_SUITE_RETURN_CODE=", cp.returncode)
tail = OUT.read_text(errors="ignore").splitlines()[-180:]
print("FULL_SUITE_TAIL_BEGIN")
print("\n".join(tail))
print("FULL_SUITE_TAIL_END")
print("FULL_SUITE_OUTPUT=", OUT)

if cp.returncode == 0:
    print("FULL_SUITE=PASS")
else:
    print("FULL_SUITE=NEXT_FAILURE_FOUND")

print("SOURCE_RESTORED=FALSE")
print("V65_58_COMPLETE")
PY
