from pathlib import Path
import sys

ROOT = Path.home() / "companyos"
sys.path.insert(0, str(ROOT))

from companyos_modules.final_consolidation.runtime import CompanyOSConsolidatedRuntime


def runtime():
    return CompanyOSConsolidatedRuntime(
        ROOT / "companyos_runtime" / "final_consolidation_test"
    )


def test_manifest_preserves_action_gates():
    manifest = runtime().deployment_manifest()
    assert manifest["external_actions_default"] is False
    assert manifest["financial_actions_default"] is False
    assert manifest["rollback_required"] is True


def test_integration_state_preserves_existing_gates():
    state = runtime().integration_state()
    assert state["external_actions_require_existing_gate"] is True
    assert state["financial_actions_require_existing_gate"] is True


def test_component_audit_has_expected_stack():
    results = runtime().component_audit()
    names = {item.name for item in results}
    assert "controlled_launch" in names
    assert "enterprise_orchestrator" in names
    assert "venture_scheduler" in names
    assert "executive_mission_control" in names
    assert "enterprise_learning_engine" in names
    assert "strategy_evolution" in names


def test_verification_writes_result():
    result = runtime().verify()
    assert "checks" in result
    assert result["checks"]["external_gate_preserved"] is True
    assert result["checks"]["financial_gate_preserved"] is True
