#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
FILE="companyos/runtime/runtime_control.py"
TEST="tests/generated/test_runtime_control_pid_ownership_v65_10.py"
STAMP="$(date +%Y%m%d_%H%M%S)"
cp "$FILE" "${FILE}.v65_10_backup_${STAMP}"

python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/runtime_control.py")
s=p.read_text()
needle="    def _log(self, message: str) -> None:\n"
if "_pid_is_companyos_supervisor" not in s:
    helper = (
        "    @staticmethod\n"
        "    def _pid_is_companyos_supervisor(pid: int | None) -> bool:\n"
        "        if not UnifiedRuntimeControl._pid_alive(pid):\n"
        "            return False\n"
        "        try:\n"
        "            raw = Path(f\"/proc/{int(pid)}/cmdline\").read_bytes()\n"
        "            cmd = raw.replace(b\"\\x00\", b\" \").decode(\"utf-8\", errors=\"replace\")\n"
        "        except (OSError, ValueError, TypeError):\n"
        "            return False\n"
        "        normalized = cmd.replace(\"\\\\\", \"/\")\n"
        "        return (\"companyos/runtime/service_supervisor.py\" in normalized\n"
        "                or \"companyos.runtime.service_supervisor\" in normalized)\n\n"
    )
    if needle not in s:
        raise SystemExit("PATCH_ABORT=_log insertion point not found")
    s=s.replace(needle, helper+needle, 1)

old="        supervisor_alive = self._pid_alive(pid)\n"
if old not in s:
    raise SystemExit("PATCH_ABORT=status supervisor line not found")
s=s.replace(old, "        supervisor_alive = self._pid_is_companyos_supervisor(pid)\n", 1)

old2 = """        pid = before.get("supervisor_pid")
        if self._pid_alive(pid):
            try:
                os.kill(int(pid), signal.SIGTERM)
            except ProcessLookupError:
                pass
"""
new2 = """        pid = before.get("supervisor_pid")
        if self._pid_is_companyos_supervisor(pid):
            try:
                os.kill(int(pid), signal.SIGTERM)
            except ProcessLookupError:
                pass
        elif pid:
            self._log(f"STALE/FOREIGN supervisor pid ignored: {pid}")
            self.pid_path.unlink(missing_ok=True)
"""
if old2 not in s:
    raise SystemExit("PATCH_ABORT=stop signal block not found")
s=s.replace(old2,new2,1)
p.write_text(s)
PY

mkdir -p tests/generated
cat > "$TEST" <<'PY'
from pathlib import Path
from companyos.runtime.runtime_control import UnifiedRuntimeControl

def test_foreign_live_pid_is_not_supervisor(monkeypatch):
    monkeypatch.setattr(UnifiedRuntimeControl, "_pid_alive", staticmethod(lambda pid: True))
    monkeypatch.setattr(Path, "read_bytes", lambda self: b"python\\x00other_program.py\\x00")
    assert UnifiedRuntimeControl._pid_is_companyos_supervisor(12345) is False

def test_companyos_supervisor_pid_is_recognized(monkeypatch):
    monkeypatch.setattr(UnifiedRuntimeControl, "_pid_alive", staticmethod(lambda pid: True))
    monkeypatch.setattr(Path, "read_bytes", lambda self: b"python\\x00companyos/runtime/service_supervisor.py\\x00")
    assert UnifiedRuntimeControl._pid_is_companyos_supervisor(12345) is True

def test_dead_pid_is_not_supervisor(monkeypatch):
    monkeypatch.setattr(UnifiedRuntimeControl, "_pid_alive", staticmethod(lambda pid: False))
    assert UnifiedRuntimeControl._pid_is_companyos_supervisor(12345) is False
PY

python -m py_compile "$FILE"
pytest -q "$TEST"
git diff --check
echo "V65_10_PID_OWNERSHIP_GUARD=PASS"
echo "BACKUP=${FILE}.v65_10_backup_${STAMP}"
