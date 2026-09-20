#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"; export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V65.9 RUNTIME CONTROL PID HELPER ====="
F="companyos/runtime_control.py"
test -f "$F" || { echo "V65_9_ABORT=$F not found"; exit 1; }
cp "$F" "$F.v65_9_backup_$(date +%Y%m%d_%H%M%S)"
grep -nE 'pid_is_alive|os\.kill|/proc/|process' "$F" | head -80 || true
python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime_control.py")
s=p.read_text()
if "def _pid_is_alive(" in s:
    print("PID_HELPER_ALREADY_PRESENT=1")
elif "def pid_is_alive(" in s:
    s += "\n\n# Backward-compatible private API expected by stale-PID recovery.\n_pid_is_alive = pid_is_alive\n"
    p.write_text(s)
    print("PID_HELPER_ALIAS_ADDED=1")
else:
    lines = [
        "", "",
        "# Backward-compatible PID liveness helper used by stale-PID recovery.",
        "def _pid_is_alive(pid: int) -> bool:",
        "    try:",
        "        pid = int(pid)",
        "    except (TypeError, ValueError):",
        "        return False",
        "    if pid <= 0:",
        "        return False",
        "    try:",
        "        import os",
        "        os.kill(pid, 0)",
        "    except ProcessLookupError:",
        "        return False",
        "    except PermissionError:",
        "        return True",
        "    except OSError:",
        "        return False",
        "    return True",
        "",
    ]
    p.write_text(s + "\n".join(lines))
    print("PID_HELPER_IMPLEMENTED=1")
PY
python -m py_compile "$F"
python - <<'PY'
from companyos.runtime_control import _pid_is_alive
import os
assert _pid_is_alive(os.getpid()) is True
assert _pid_is_alive(-1) is False
print("PID_HELPER_SMOKE=PASS")
PY
python -m pytest -q tests/test_runtime_control_stale_pid_recovery_v21.py --disable-warnings --maxfail=1
git diff --check
echo "V65_9_STALE_PID_RECOVERY=PASS"
echo "===== NEXT FULL-SUITE FAILURE ====="
python -m pytest -q tests --disable-warnings --maxfail=1
echo "V65_9_FULL_SUITE=PASS"
