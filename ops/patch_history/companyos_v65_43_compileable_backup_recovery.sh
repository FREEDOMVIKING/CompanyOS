#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
TARGET="companyos/runtime/capability_expansion.py"

echo "===== COMPANYOS V65.43 COMPILEABLE BACKUP RECOVERY ====="

python - <<'PY'
from pathlib import Path
import py_compile, shutil, time

target=Path("companyos/runtime/capability_expansion.py")
candidates=sorted(
    target.parent.glob(target.name+".v65_*backup*"),
    key=lambda p:p.stat().st_mtime,
    reverse=True
)

print("BACKUPS_FOUND=", len(candidates))
good=[]
for p in candidates:
    try:
        py_compile.compile(str(p), doraise=True)
        print("COMPILEABLE=", p)
        good.append(p)
    except Exception as e:
        print("BROKEN=", p, "::", str(e).splitlines()[-1])

if not good:
    raise SystemExit("ABORT=no compileable V65 backup found")

chosen=good[0]
safety=target.with_name(target.name+f".v65_43_broken_snapshot_{int(time.time())}")
shutil.copy2(target, safety)
shutil.copy2(chosen, target)
py_compile.compile(str(target), doraise=True)

print("CHOSEN_BACKUP=", chosen)
print("BROKEN_SNAPSHOT=", safety)
print("BASELINE_COMPILE=PASS")
PY

echo "===== IMPORT CHECK ====="
python - <<'PY'
import inspect
import companyos.runtime.capability_expansion as ce
print("IMPORT=PASS")
print("TEST_STAGE_SIGNATURE=", inspect.signature(ce.test_stage))
print("TEST_STAGE_SOURCE_BEGIN")
print(inspect.getsource(ce.test_stage))
print("TEST_STAGE_SOURCE_END")
PY

echo "V65_43_RECOVERY=PASS"
