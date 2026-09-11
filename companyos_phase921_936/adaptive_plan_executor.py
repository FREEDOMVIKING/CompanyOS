from .strategy_task_dispatcher import StrategyTaskDispatcher
class AdaptivePlanExecutor:
    """921: execute every task in an adaptive revalidation plan."""
    def execute(self, strategy, provider_results=None):
        tasks=list(((strategy or {}).get("plan") or {}).get("tasks",[]) or [])
        results=[]
        for task in tasks:
            results.append(StrategyTaskDispatcher().dispatch(task, provider_results or {}))
        return results
