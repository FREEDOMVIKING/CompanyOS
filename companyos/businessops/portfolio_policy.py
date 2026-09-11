class PortfolioPolicy:
    def decide(self, metrics):
        revenue = float(metrics.get("revenue",0) or 0)
        cost = float(metrics.get("cost",0) or 0)
        profit = float(metrics.get("profit", revenue-cost) or 0)

        if profit > 0 and revenue > 0:
            action = "scale"
        elif cost > 0 and profit < 0:
            action = "review_or_kill"
        else:
            action = "continue_validation"

        return {
            "action": action,
            "reinvest_allowed": action == "scale",
            "requires_human_approval_for_irreversible_actions": True
        }
