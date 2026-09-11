class UnitEconomicsEngine:
    def evaluate(self, revenue, variable_cost, acquisition_cost, customers):
        customers=max(1,int(customers))
        gross=float(revenue)-float(variable_cost)
        contribution=gross-float(acquisition_cost)
        return {
            "gross_profit":round(gross,2),
            "contribution_profit":round(contribution,2),
            "revenue_per_customer":round(float(revenue)/customers,2),
            "profitable":contribution>0
        }
