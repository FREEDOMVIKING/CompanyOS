from companyos_phase905_920 import CEOAdaptiveRecoveryBridge
from companyos_phase921_936 import CEOAdaptiveExecutionBridge

class AdaptiveResearchSupervisor:
    """945-952: run bounded adaptive research strategy rounds."""
    def __init__(self, root):
        self.root = root

    def run(self, mission, validation, provider_results=None, max_rounds=3):
        history = list(((mission.get("context") or {}).get("revalidation_history")) or [])
        strategy_history = []
        execution_history = []
        rounds = []
        current_validation = validation
        current_mission = mission

        for round_no in range(1, int(max_rounds)+1):
            strategy = CEOAdaptiveRecoveryBridge(self.root).build_strategy(
                current_mission,
                current_validation,
                history=history,
                strategy_history=strategy_history,
                round_no=round_no,
            )
            strategy_history.append({
                "query": strategy.get("query"),
                "providers": strategy.get("providers"),
            })
            execution = CEOAdaptiveExecutionBridge(self.root).run(
                current_mission,
                current_validation,
                provider_results or {},
                history=history,
                strategy_history=strategy_history[:-1],
                strategy_attempt=round_no,
                execution_history=execution_history,
            )
            execution_history = execution.get("execution_history", execution_history)
            current_validation = execution.get("validation", current_validation)
            current_mission = execution.get("updated_mission", current_mission)
            rounds.append(execution)

            decision = (execution.get("decision") or {}).get("decision")
            if decision in ("GO","KILL","HUMAN_REVIEW"):
                break

        return {
            "rounds": rounds,
            "final_validation": current_validation,
            "updated_mission": current_mission,
            "strategy_history": strategy_history,
            "execution_history": execution_history,
        }
