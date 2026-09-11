class BudgetGovernor:
    def evaluate(self, request, free_cash, runway_months, autonomous_limit=500):
        amount=float(request.get("amount",0))
        allowed=(amount<=float(autonomous_limit) and amount<=float(free_cash)*0.2 and float(runway_months)>=6)
        return {"allowed":allowed,"requires_approval":not allowed,
                "reason":"within_budget_policy" if allowed else "budget_policy_limit"}
