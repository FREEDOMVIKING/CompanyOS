from pathlib import Path
import tempfile
from companyos.capabilityops import CapabilityPolicy, CapabilityRegistry, RealExecutionBridge

def test_policy_gate():
    assert CapabilityPolicy().evaluate("production_deploy",approval=False)["allowed"] is False

def test_registry():
    assert "research" in CapabilityRegistry().build()

def test_internal_fallback_without_provider():
    root=Path(tempfile.mkdtemp())
    r=RealExecutionBridge(root).execute({"job_id":"x","kind":"research","payload":{}},"research")
    assert r["success"] is True
    assert r["mode"]=="internal_fallback"
