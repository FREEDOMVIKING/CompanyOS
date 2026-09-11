from companyos_phase705_720 import ContextBus, GovernedActionRouter, UnifiedRuntimeStatus
import tempfile
from pathlib import Path

def test_context_bus():
    assert ContextBus().merge({"x":1},{"y":2}) == {"x":1,"y":2}

def test_governance_router():
    root = Path(tempfile.mkdtemp())
    router = GovernedActionRouter(root)
    assert router.route({"action_type":"research"})["allowed"] is True
    assert router.route({"action_type":"sign_contract"})["allowed"] is False

def test_runtime():
    assert UnifiedRuntimeStatus().status()["status"] == "phase720_unified_autonomous_ceo_runtime_ready"
