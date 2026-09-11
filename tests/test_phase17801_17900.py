from pathlib import Path
import sys

ROOT = Path.home() / "companyos"
sys.path.insert(0, str(ROOT))

from companyos_modules.phase17801_17900.controlled_launch import ControlledLaunchManager


def manager():
    return ControlledLaunchManager(ROOT / "companyos_runtime/phase17801_17900_test")


def test_controlled_beta_requires_core_checks():
    state = manager().evaluate(
        phase_verified=True,
        tests_passed=True,
        state_persistent=True,
        start_stop_present=True,
        local_ai_ok=True,
        soak_passed=False,
    )
    assert state.ready_for_controlled_beta is True
    assert state.ready_for_external_launch is False
    assert "extended_soak_test_incomplete" in state.blockers


def test_external_launch_requires_explicit_approval():
    state = manager().evaluate(
        phase_verified=True,
        tests_passed=True,
        state_persistent=True,
        start_stop_present=True,
        local_ai_ok=True,
        soak_passed=True,
        explicit_external_approval=False,
    )
    assert state.ready_for_external_launch is False
    assert "explicit_external_launch_approval_required" in state.blockers


def test_external_launch_can_pass_without_bypassing_gates():
    state = manager().evaluate(
        phase_verified=True,
        tests_passed=True,
        state_persistent=True,
        start_stop_present=True,
        local_ai_ok=True,
        soak_passed=True,
        explicit_external_approval=True,
    )
    assert state.stage == "EXTERNAL_LAUNCH_READY"
    assert state.external_actions_require_existing_gate is True
    assert state.financial_actions_require_existing_gate is True


def test_manifest_defaults_are_safe():
    manifest = manager().deployment_manifest()
    assert manifest["local_ai_endpoint"].endswith(":8080")
    assert manifest["external_actions_default"] is False
    assert manifest["financial_actions_default"] is False
    assert manifest["rollback_required"] is True
