from __future__ import annotations

from companyos.runtime.autonomous_task_dispatcher import AutonomousTaskDispatcher


def register_default_specialists(dispatcher: AutonomousTaskDispatcher) -> None:
    """
    Minimal internal specialist registry for Phase 95 validation.

    These are safe, deterministic internal handlers only.
    Future phases can replace them with real specialist-agent adapters.
    """

    def research_handler(task):
        topic = str(task.payload.get("topic", "")).strip()
        return {
            "agent": "research_agent",
            "task_type": task.task_type,
            "summary": f"research_stub_completed:{topic}",
        }

    def planning_handler(task):
        goal = str(task.payload.get("goal", "")).strip()
        return {
            "agent": "planning_agent",
            "task_type": task.task_type,
            "plan": [
                f"clarify:{goal}",
                f"decompose:{goal}",
                f"execute:{goal}",
                f"review:{goal}",
            ],
        }

    def build_handler(task):
        name = str(task.payload.get("name", "")).strip()
        return {
            "agent": "builder_agent",
            "task_type": task.task_type,
            "artifact": f"build_stub:{name}",
        }

    dispatcher.register(
        task_type="research",
        agent_name="research_agent",
        handler=research_handler,
    )
    dispatcher.register(
        task_type="planning",
        agent_name="planning_agent",
        handler=planning_handler,
    )
    dispatcher.register(
        task_type="build",
        agent_name="builder_agent",
        handler=build_handler,
    )
