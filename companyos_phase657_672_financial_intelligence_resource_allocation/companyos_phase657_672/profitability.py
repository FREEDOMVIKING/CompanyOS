class Profitability:
    """659: profitability summary."""

    def calculate(self, snapshot):
        revenue=float(snapshot.get("revenue",0))
        costs=float(snapshot.get("variable_costs",0))+float(snapshot.get("fixed_costs",0))+float(snapshot.get("acquisition_spend",0))
        profit=revenue-costs
        return {
            "revenue":round(revenue,2),
            "costs":round(costs,2),
            "profit":round(profit,2),
            "profit_margin":round(profit/revenue,4) if revenue>0 else None,
            "profitable":profit>0,
        }
