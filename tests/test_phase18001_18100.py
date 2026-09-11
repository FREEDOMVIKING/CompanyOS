from pathlib import Path
import sys

ROOT = Path.home() / "companyos"
sys.path.insert(0, str(ROOT))

from companyos_modules.phase18001_18100.venture_scheduler import (
    VentureScheduler,
    VentureTask,
)


def scheduler():
    return VentureScheduler(
        ROOT / "companyos_runtime" / "phase18001_18100_test"
    )


def sample_tasks():
    return [
        VentureTask(
            "a",
            "alpha",
            "Discover",
            90,
            0.80,
            0.20,
            2,
            [],
            ["research"],
        ),
        VentureTask(
            "b",
            "alpha",
            "Build",
            85,
            0.75,
            0.25,
            4,
            ["a"],
            ["python"],
        ),
        VentureTask(
            "c",
            "beta",
            "Blocked",
            99,
            0.95,
            0.10,
            1,
            [],
            ["research"],
            blocked=True,
        ),
    ]


def test_dependency_order_is_respected():
    decisions = scheduler().schedule(
        sample_tasks(),
        capability_pool={"research", "python"},
        max_parallel=1,
    )
    scheduled = [item for item in decisions if item.action == "schedule"]
    assert [item.task_id for item in scheduled] == ["a", "b"]


def test_blocked_task_is_held():
    decisions = scheduler().schedule(
        sample_tasks(),
        capability_pool={"research", "python"},
    )
    blocked = next(item for item in decisions if item.task_id == "c")
    assert blocked.action == "hold"
    assert blocked.reason == "task_blocked"


def test_missing_capability_creates_recovery_action():
    tasks = [
        VentureTask(
            "x",
            "gamma",
            "Deploy",
            90,
            0.90,
            0.20,
            2,
            [],
            ["deployment"],
        )
    ]
    s = scheduler()
    decisions = s.schedule(tasks, capability_pool={"python"})
    recovery = s.recovery_plan(decisions)
    assert recovery["actions"][0]["action"] == "request_internal_specialist"
    assert recovery["external_actions_require_existing_gate"] is True
    assert recovery["financial_actions_require_existing_gate"] is True


def test_demo_returns_executive_plan():
    result = scheduler().demo()
    assert result["ok"] is True
    assert result["executive_plan"]["decision"] in {
        "execute_internal_schedule",
        "repair_before_scheduling",
    }
