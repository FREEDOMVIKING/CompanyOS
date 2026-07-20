class FinanceController:
    """79: budget/runway guardrails; planning only, no fund movement."""
    def assess(self,cash,monthly_burn,planned_spend=0):
        cash=max(0,float(cash)); burn=max(0,float(monthly_burn)); spend=max(0,float(planned_spend))
        remaining=max(0,cash-spend)
        runway=(remaining/burn) if burn else None
        return {"cash":cash,"planned_spend":spend,"remaining":round(remaining,2),
                "runway_months":None if runway is None else round(runway,2),
                "spend_requires_approval":spend>0,"funds_moved":False}
