class CashflowGuard:
    """1183-1192: prevent autonomous overspending and preserve runway."""
    def evaluate(self, financials, proposed_spend, min_runway_months=6, max_free_cash_share=0.2):
        free_cash=float(financials.get("free_cash",0))
        runway=float(financials.get("runway_months",0))
        max_by_cash=free_cash*float(max_free_cash_share)
        allowed=runway>=float(min_runway_months) and float(proposed_spend)<=max_by_cash
        return {
            "allowed":allowed,
            "max_autonomous_spend":round(max_by_cash,2),
            "requires_approval":not allowed,
            "reason":"within_cashflow_policy" if allowed else "cashflow_or_runway_limit",
        }
