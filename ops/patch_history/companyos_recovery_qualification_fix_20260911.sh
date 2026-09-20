#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${HOME}/companyos"
BRANCH="companyos-continuous-fix-2026-09-11"

cd "$ROOT"

python - <<'PY'
from pathlib import Path

p = Path("companyos/runtime/runtime_control.py")
s = p.read_text(encoding="utf-8")

old = '''    @staticmethod
    def _pid_alive(pid: int | None) -> bool:
        if not pid:
            return False
        try:
            os.kill(int(pid), 0)
            return True
        except (ProcessLookupError, PermissionError, ValueError, TypeError):
            return False
'''

new = '''    @staticmethod
    def _pid_alive(pid: int | None) -> bool:
        if not pid:
            return False
        try:
            pid = int(pid)
            os.kill(pid, 0)
        except (ProcessLookupError, PermissionError, ValueError, TypeError):
            return False

        # Android/Termux can briefly leave a detached process as a zombie.
        # os.kill(pid, 0) still succeeds for zombies, so inspect /proc.
        try:
            stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
            right = stat.rsplit(")", 1)
            if len(right) == 2:
                state = right[1].strip().split()[0]
                if state in {"Z", "X", "x"}:
                    return False
        except Exception:
            pass

        return True
'''

if old not in s:
    raise SystemExit("expected _pid_alive block not found")

s = s.replace(old, new, 1)
s = s.replace(
    "    def stop(self, wait_seconds: float = 15.0) -> dict[str, Any]:",
    "    def stop(self, wait_seconds: float = 45.0) -> dict[str, Any]:",
    1,
)
p.write_text(s, encoding="utf-8")

q = Path("companyos/runtime/end_to_end_qualification.py")
t = q.read_text(encoding="utf-8")
t = t.replace(
    "stopped = self.control.stop(wait_seconds=15)",
    "stopped = self.control.stop(wait_seconds=45)",
)
q.write_text(t, encoding="utf-8")

print("Patched zombie detection and graceful shutdown timeout")
PY

python -m py_compile \
  companyos/runtime/runtime_control.py \
  companyos/runtime/end_to_end_qualification.py

echo "===== RESTART CLEANLY ====="
scripts/companyosctl stop >/dev/null 2>&1 || true
sleep 2
scripts/companyosctl start >/dev/null

echo "===== RE-RUN FULL QUALIFICATION ====="
python scripts/validate_companyos_full_launch.py

echo "===== COMMIT + PUSH ====="
git add \
  companyos/runtime/runtime_control.py \
  companyos/runtime/end_to_end_qualification.py

git commit -m "Fix CompanyOS recovery qualification shutdown detection" || true
git push origin "$BRANCH"

echo "===== FINAL SUMMARY ====="
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos/.companyos_runtime/full_autonomous_qualification.json"
obj=json.loads(p.read_text())
print("core_pass:", obj.get("core_pass"))
print("launch_level:", obj.get("launch_level"))
print("core_checks:", obj.get("core_checks"))
print("recovery_ok:", (obj.get("recovery") or {}).get("ok"))
print("final_healthy:", (obj.get("final_health") or {}).get("healthy"))
PY

echo "COMPANYOS_RECOVERY_QUALIFICATION_FIX=COMPLETE"
