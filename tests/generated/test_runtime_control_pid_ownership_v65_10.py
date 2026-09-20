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
