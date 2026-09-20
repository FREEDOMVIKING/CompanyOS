#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"; export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V65.8 RUNTIME CONTROL PID API ====="
F="companyos/runtime_control/__init__.py"
cp "$F" "$F.v65_8_backup_$(date +%Y%m%d_%H%M%S)"
echo "--- locate pid_is_alive ---"
grep -RIn --exclude-dir=.git --exclude='*.pyc' -E 'def[[:space:]]+_?pid_is_alive|_?pid_is_alive[[:space:]]*=' companyos/runtime_control companyos 2>/dev/null | head -40 || true
python - <<'PY'
from pathlib import Path
pkg=Path("companyos/runtime_control")
init=pkg/"__init__.py"
s=init.read_text()
if "pid_is_alive" in s:
    print("PID_EXPORT_ALREADY_PRESENT=1")
else:
    hits=[]
    for q in pkg.glob("*.py"):
        txt=q.read_text(errors="ignore")
        if "def pid_is_alive" in txt:
            hits.append((q,"pid_is_alive"))
        elif "def _pid_is_alive" in txt:
            hits.append((q,"_pid_is_alive"))
    if not hits:
        raise SystemExit("V65_8_ABORT=pid_is_alive implementation not found")
    q,name=hits[0]
    mod="companyos.runtime_control."+q.stem
    if name=="pid_is_alive":
        s += f"\nfrom {mod} import pid_is_alive\n"
    else:
        s += f"\nfrom {mod} import _pid_is_alive as pid_is_alive\n"
    init.write_text(s)
    print("PID_EXPORT_SOURCE="+mod+"."+name)
PY
python -m py_compile "$F"
python -m pytest -q tests/test_runtime_control_stale_pid_recovery_v21.py --disable-warnings --maxfail=1
git diff --check
echo "V65_8_RUNTIME_CONTROL_PID_API=PASS"
echo "===== NEXT FULL-SUITE FAILURE ====="
python -m pytest -q tests --disable-warnings --maxfail=1
echo "V65_8_FULL_SUITE=PASS"
