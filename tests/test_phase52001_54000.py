from pathlib import Path
import tempfile
from companyos.controlledexec import PostExecutionLock, ControlledExecutionStatus

def test_postlock():
    root=Path(tempfile.mkdtemp())
    p=PostExecutionLock(root)
    assert p.status()["locked"] is False
    p.engage("x")
    assert p.status()["locked"] is True

def test_status_safe_default():
    s=ControlledExecutionStatus().status()
    assert s["autonomous_live_enabled"] is False
    assert s["broadcast_adapter_integration_ready"] is False
