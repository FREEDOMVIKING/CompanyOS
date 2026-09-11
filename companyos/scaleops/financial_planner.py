class FinancialPlanner:
    def plan(self, revenue, cogs, opex, growth_investment=0):
        revenue=float(revenue); cogs=float(cogs); opex=float(opex); growth_investment=float(growth_investment)
        gross_profit=revenue-cogs
        operating_profit=gross_profit-opex-growth_investment
        return {
            "revenue":revenue,
            "gross_profit":round(gross_profit,2),
            "operating_profit":round(operating_profit,2),
            "gross_margin":round(gross_profit/revenue,3) if revenue else 0,
            "growth_investment":growth_investment
        }
