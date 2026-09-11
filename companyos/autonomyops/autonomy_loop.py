from .objective_engine import ObjectiveEngine
from .cycle_memory import CycleMemory

class AutonomousLoop:
    def __init__(self, root, ceo_orchestrator, queue, worker_pool):
        self.root = root
        self.ceo = ceo_orchestrator
        self.queue = queue
        self.worker_pool = worker_pool
        self.memory = CycleMemory(root)

    def run_cycle(self, objective=None, context=None, max_jobs=25):
        recent = self.memory.recent(20)
        objective = objective or ObjectiveEngine().choose(recent)

        plan = self.ceo.plan_and_delegate(
            objective,
            self.queue,
            context=context or {
                "mode": "continuous_autonomous_internal_operation",
                "external_side_effects": "approval_gated"
            }
        )

        output = {
            "objective": objective,
            "plan_cycle": plan
        }

        if plan.get("success"):
            execution = self.ceo.execute_delegated(
                self.queue,
                self.worker_pool,
                max_jobs=max_jobs
            )
            output["execution_cycle"] = execution
            summary = execution.get("verification_summary", {})
            output["resolved"] = bool(summary.get("cycle_verified"))
            output["next_action"] = (
                "continue_autonomous_cycle"
                if summary.get("cycle_verified")
                else "analyze_unresolved_and_recover"
            )
        else:
            output["resolved"] = False
            output["next_action"] = "recover_planning_failure"

        self.memory.append(output)
        return output
