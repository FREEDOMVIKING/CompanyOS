#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.46 FIX STAGE CONTRACT TUPLE SHAPE ====="

python - <<'PY'
from pathlib import Path
import shutil, time, py_compile, subprocess, sys

ROOT=Path.home()/"companyos"
SRC=ROOT/"companyos/runtime/capability_expansion.py"
BACKUP=SRC.with_name(f"capability_expansion.py.v65_46_backup_{int(time.time())}")

text=SRC.read_text()
shutil.copy2(SRC, BACKUP)
print("BACKUP=", BACKUP)

old = "    return (cid, root, sorted(set(errors)), gap_plan)"
new = '''    # Public stage_plan contract: (capability_id, staging_root, errors)
    # gap_plan remains internal; existing callers/tests consume a 3-tuple.
    return (cid, root, sorted(set(errors)))'''

if old not in text:
    print("V65_46_ABORT=expected_return_contract_not_found")
    raise SystemExit(2)

SRC.write_text(text.replace(old,new,1))
print("PATCH=stage_plan_4tuple_to_3tuple")

try:
    py_compile.compile(str(SRC), doraise=True)
    print("PY_COMPILE=PASS")
except Exception:
    shutil.copy2(BACKUP,SRC)
    print("PY_COMPILE=FAIL_RESTORED")
    raise

target=ROOT/"tests/test_capability_expansion_test_recovery_v5.py"
cp=subprocess.run(
    [sys.executable,"-m","pytest","-q",
     str(target)+"::CapabilityExpansionTestRecoveryV5::test_staged_contract_executes"],
    cwd=str(ROOT),text=True,capture_output=True,timeout=90
)
print("TARGET_RETURN_CODE=",cp.returncode)
print(cp.stdout[-10000:])
print(cp.stderr[-4000:])

if cp.returncode != 0:
    shutil.copy2(BACKUP,SRC)
    print("TARGET_TEST=FAIL")
    print("SOURCE_RESTORED=TRUE")
    raise SystemExit(cp.returncode)

print("TARGET_TEST=PASS")

cp2=subprocess.run(
    [sys.executable,"-m","pytest","-q",str(target)],
    cwd=str(ROOT),text=True,capture_output=True,timeout=120
)
print("RECOVERY_V5_RETURN_CODE=",cp2.returncode)
print(cp2.stdout[-12000:])
print(cp2.stderr[-4000:])

if cp2.returncode != 0:
    shutil.copy2(BACKUP,SRC)
    print("RECOVERY_V5=FAIL")
    print("SOURCE_RESTORED=TRUE")
    raise SystemExit(cp2.returncode)

print("RECOVERY_V5=PASS")
print("SOURCE_RESTORED=FALSE")
print("V65_46_COMPLETE")
PY
