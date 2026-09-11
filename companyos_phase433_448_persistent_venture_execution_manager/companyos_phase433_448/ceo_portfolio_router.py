from .execution_manager import ExecutionManager

class CEOPortfolioRouter:
    """447: CEO-level resource routing across ventures."""

    def route(self, ventures, max_active=2):
        plan = ExecutionManager().manage(ventures, max_active=max_active)
        active = plan["allocation"]["active"]
        return {
            **plan,
            "ceo_directive":{
                "fund_attention_to":[v.get("venture_id") for v in active],
                "defer":[v.get("venture_id") for v in plan["allocation"]["waiting"]],
                "rule":"prioritize strongest validated ventures while preserving bounded capacity",
            },
        }
