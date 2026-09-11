from .stage_router import StageRouter
from .stage_contract import StageContract
from .cycle_budget import CycleBudget
from .failure_recovery import FailureRecovery
from .system_bridge import SystemBridge

class CEOCycle:
    """478: one bounded multi-stage CEO operating cycle."""

    def __init__(self, root):
        self.bridge = SystemBridge(root)
        self.router = StageRouter()
        self.contract = StageContract()
        self.budget = CycleBudget()
        self.recovery = FailureRecovery()

    def run(self, start_stage="opportunity", context=None):
        context = dict(context or {})
        stage = start_stage
        history = []
        failures = 0
        limits = self.budget.limits()

        for _ in range(limits["max_stages_per_cycle"]):
            result = self.contract.normalize(self.bridge.run_stage(stage, context), stage)
            history.append(result)

            if not result["success"]:
                failures += 1
                recovery = self.recovery.decide(failures, stage)
                if recovery["action"] == "pause_cycle":
                    break
            else:
                data = result.get("data") or {}
                context.update(data)

            next_stage = self.router.next_stage(stage, result)

            if next_stage == stage and result.get("status") in (
                "validation_plan_ready",
                "operations_waiting_for_metrics",
                "no_opportunity_candidate",
            ):
                break

            stage = next_stage

        return {
            "success": bool(history) and any(x.get("success") for x in history),
            "status":"ceo_cycle_completed",
            "start_stage":start_stage,
            "end_stage":stage,
            "failures":failures,
            "history":history,
            "context":context,
        }
