class FinancialController:
    """1171-1182: P&L, runway, margin, and controlled spend recommendations."""
    def compute(self, cash, revenue, cogs, opex, committed_spend=0):
        revenue=float(revenue); cogs=float(cogs); opex=float(opex); cash=float(cash)
        gross_profit=revenue-cogs
        operating_profit=gross_profit-opex
        burn=max(0,opex+cogs-revenue)
        runway=(cash/max(1,burn)) if burn>0 else 999
        gross_margin=(gross_profit/revenue) if revenue>0 else 0
        free_cash=max(0,cash-float(committed_spend))
        return {
            "gross_profit":round(gross_profit,2),
            "operating_profit":round(operating_profit,2),
            "burn":round(burn,2),
            "runway_months":round(runway,2),
            "gross_margin":round(gross_margin,3),
            "free_cash":round(free_cash,2),
        }
