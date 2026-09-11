class BudgetEnforcer:
    def evaluate(self, action, available_budget, reserve_ratio=.2):
        amount=float(action.get("amount",0) or 0)
        available=float(available_budget)
        reserve=available*float(reserve_ratio)
        allowed=amount<=max(0,available-reserve)
        return {
            "allowed":allowed,
            "amount":amount,
            "available_budget":available,
            "reserve":round(reserve,2)
        }
