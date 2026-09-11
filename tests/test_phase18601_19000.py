from pathlib import Path
import sys

ROOT = Path.home() / "companyos"
sys.path.insert(0, str(ROOT))

from companyos_modules.phase18601_19000.autonomous_operations_kernel import (
    AutonomousOperationsKernel,
    WorkItem,
)


def kernel(name: str) -> AutonomousOperationsKernel:
    return AutonomousOperationsKernel(
        ROOT / "companyos_runtime" / "phase18601_19000_test" / name
    )


def test_internal_work_executes():
    k = kernel("internal")
    k.enqueue([
        WorkItem(
            "a", "alpha", "Research", 90, 0.8, 0.2, [], ["research"]
        )
    ])
    result = k.run_cycle(capabilities={"research"})
    assert result["executed_count"] == 1


def test_external_action_is_held():
    k = kernel("external")
    k.enqueue([
        WorkItem(
            "a",
            "alpha",
            "Publish",
            90,
            0.8,
            0.2,
            [],
            ["deployment"],
            external_action=True,
        )
    ])
    result = k.run_cycle(capabilities={"deployment"})
    assert result["held_for_gate_count"] == 1
    assert result["results"][0]["status"] == "awaiting_existing_gate"


def test_financial_action_is_held():
    k = kernel("financial")
    k.enqueue([
        WorkItem(
            "a",
            "alpha",
            "Transfer",
            90,
            0.8,
            0.2,
            [],
            ["finance"],
            financial_action=True,
        )
    ])
    result = k.run_cycle(capabilities={"finance"})
    assert result["held_for_gate_count"] == 1


def test_dependency_order():
    k = kernel("dependencies")
    k.enqueue([
        WorkItem("a", "alpha", "Research", 90, 0.8, 0.2, [], ["research"]),
        WorkItem("b", "alpha", "Build", 85, 0.7, 0.2, ["a"], ["python"]),
    ])
    first = k.run_cycle(capabilities={"research", "python"}, max_items=1)
    second = k.run_cycle(capabilities={"research", "python"}, max_items=1)
    assert first["results"][0]["work_id"] == "a"
    assert second["results"][0]["work_id"] == "b"


def test_demo_preserves_all_gates():
    result = kernel("demo_wrapper").demo()
    status = result["status"]
    assert status["external_actions_enabled"] is False
    assert status["financial_actions_enabled"] is False
    assert status["irreversible_actions_enabled"] is False
