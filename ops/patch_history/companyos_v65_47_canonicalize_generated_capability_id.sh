#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.47 CANONICALIZE GENERATED CAPABILITY ID ====="

python - <<'PY'
from pathlib import Path
import shutil, time, py_compile, subprocess, sys

ROOT = Path.home() / "companyos"
SRC = ROOT / "companyos/runtime/capability_expansion.py"
BACKUP = SRC.with_name(f"capability_expansion.py.v65_47_backup_{int(time.time())}")

text = SRC.read_text()
shutil.copy2(SRC, BACKUP)
print("BACKUP=", BACKUP)

anchor = '    module_content,test_content,shape_errors=_classify_generated_contents(plan,gap["id"])\n'

patch_lines = [
    '    module_content,test_content,shape_errors=_classify_generated_contents(plan,gap["id"])',
    '    # V65.47: generated capability source must advertise the canonical gap id,',
    '    # even when a generated candidate used a placeholder identifier.',
    '    canonical_id=normalize_capability_id(gap["id"])',
    '    if module_content is not None:',
    '        module_content=re.sub(',
    '            r"(?m)^CAPABILITY_ID\\s*=\\s*([\'\\\"]).*?\\1",',
    '            "CAPABILITY_ID="+repr(canonical_id),',
    '            module_content,',
    '            count=1,',
    '        )',
    '        module_content=re.sub(',
    '            r"([\'\\\"]id[\'\\\"]\\s*:\\s*)([\'\\\"]).*?\\2",',
    '            lambda m: m.group(1)+repr(canonical_id),',
    '            module_content,',
    '            count=1,',
    '        )',
]
patch = "\n".join(patch_lines) + "\n"

if anchor not in text:
    print("V65_47_ABORT=stage_plan_anchor_not_found")
    raise SystemExit(2)

SRC.write_text(text.replace(anchor, patch, 1))
print("PATCH=canonicalize_CAPABILITY_ID_and_manifest_id")

try:
    py_compile.compile(str(SRC), doraise=True)
    print("PY_COMPILE=PASS")
except Exception:
    shutil.copy2(BACKUP, SRC)
    print("PY_COMPILE=FAIL")
    print("SOURCE_RESTORED=TRUE")
    raise

def run(label, args, timeout=120):
    cp = subprocess.run(args, cwd=str(ROOT), text=True, capture_output=True, timeout=timeout)
    print(f"{label}_RETURN_CODE=", cp.returncode)
    if cp.stdout:
        print(cp.stdout[-14000:])
    if cp.stderr:
        print(cp.stderr[-6000:])
    return cp.returncode

target = ROOT / "tests/test_capability_expansion_test_recovery_v5.py"

rc = run(
    "TARGET_TEST",
    [
        sys.executable, "-m", "pytest", "-q",
        str(target) + "::CapabilityExpansionTestRecoveryV5::test_staged_contract_executes"
    ],
    90,
)
if rc != 0:
    shutil.copy2(BACKUP, SRC)
    print("TARGET_TEST=FAIL")
    print("SOURCE_RESTORED=TRUE")
    raise SystemExit(rc)
print("TARGET_TEST=PASS")

rc = run("RECOVERY_V5", [sys.executable, "-m", "pytest", "-q", str(target)], 120)
if rc != 0:
    shutil.copy2(BACKUP, SRC)
    print("RECOVERY_V5=FAIL")
    print("SOURCE_RESTORED=TRUE")
    raise SystemExit(rc)
print("RECOVERY_V5=PASS")

main_test = ROOT / "tests/test_capability_expansion.py"
if main_test.exists():
    rc = run("CAPABILITY_EXPANSION", [sys.executable, "-m", "pytest", "-q", str(main_test)], 120)
    if rc != 0:
        shutil.copy2(BACKUP, SRC)
        print("CAPABILITY_EXPANSION=FAIL")
        print("SOURCE_RESTORED=TRUE")
        raise SystemExit(rc)
    print("CAPABILITY_EXPANSION=PASS")

print("SOURCE_RESTORED=FALSE")
print("V65_47_COMPLETE")
PY
