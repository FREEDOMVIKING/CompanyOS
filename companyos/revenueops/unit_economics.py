class UnitEconomicsEngine:
    def calculate(self, revenue, variable_cost, acquisition_cost, retention_months):
        gross=float(revenue)-float(variable_cost)
        ltv=max(0,gross)*max(0,float(retention_months))
        cac=float(acquisition_cost)
        return {"gross_contribution":round(gross,2),"ltv":round(ltv,2),"cac":round(cac,2),
                "ltv_cac":round(ltv/cac,3) if cac else None}
