from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict

from .authority_model import AuthorityModel
from .autonomy_scheduler import AutonomyScheduler
from .builder_loop import BuilderLoop
from .self_repair import SelfRepairEngine
from .experiment_budget import ExperimentBudget
from .launch_controller import LaunchController
from .portfolio_autopilot import PortfolioAutopilot

class AutonomousCompanyLoop:
    """132: autonomy-first company loop.

    The system can research, plan, build, test, repair, experiment, and operate
    independently inside bounded reversible authority. High-impact irreversible
    actions remain gated.
    """

    def __init__(self):
        self.authority = AuthorityModel()
        self.scheduler = AutonomyScheduler()
        self.builder = BuilderLoop()
        self.repair = SelfRepairEngine()
        self.experiments = ExperimentBudget()
        self.launch = LaunchController()
        self.portfolio = PortfolioAutopilot()

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        actions = []
        for action in payload.get("actions", []):
            actions.append({**action, "authority": self.authority.evaluate(action)})

        return {
            "success": True,
            "status": "phase132_autonomous_company_loop_completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "selected_tasks": self.scheduler.select(
                payload.get("tasks", []),
                payload.get("capacity", 5),
            ),
            "build_next": self.builder.next_action(payload.get("build_state", {})),
            "repair_plan": self.repair.plan(payload.get("fault", {})),
            "experiment_authorization": self.experiments.authorize(
                payload.get("requested_cost", 0),
                payload.get("remaining_budget", 0),
                payload.get("experiment_risk", 0),
                payload.get("max_experiment_risk", 0.35),
            ),
            "launch": self.launch.evaluate(payload.get("launch", {})),
            "portfolio": self.portfolio.review(payload.get("ventures", [])),
            "actions": actions,
            "autonomy_mode": "high",
            "external_action_taken": False,
            "financial_action_taken": False,
            "irreversible_action_taken": False,
        }
