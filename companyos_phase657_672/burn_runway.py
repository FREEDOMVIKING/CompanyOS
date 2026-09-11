class BurnRunway:
    """658: burn-rate and runway intelligence."""

    def calculate(self, snapshot):
        monthly_costs = float(snapshot.get("variable_costs",0)) + float(snapshot.get("fixed_costs",0)) + float(snapshot.get("acquisition_spend",0))
        monthly_revenue = float(snapshot.get("mrr",0))
        net_burn = max(0.0, monthly_costs - monthly_revenue)
        cash = float(snapshot.get("cash_available",0))
        runway = None if net_burn <= 0 else round(cash / net_burn, 2)
        return {
            "monthly_costs": round(monthly_costs,2),
            "net_burn": round(net_burn,2),
            "runway_months": runway,
            "self_sustaining": net_burn <= 0,
        }
