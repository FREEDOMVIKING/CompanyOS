class UnitEconomics:
    """457: simple unit-economics calculations."""

    def calculate(self, metrics):
        cac = float(metrics.get("cac",0))
        arpa = float(metrics.get("arpa",0))
        gross_margin = float(metrics.get("gross_margin",0))
        monthly_churn = float(metrics.get("monthly_churn",0))
        ltv = 0.0
        if monthly_churn > 0:
            ltv = (arpa * gross_margin) / monthly_churn
        return {
            "cac":cac,
            "ltv":round(ltv,2),
            "ltv_cac_ratio":round(ltv/cac,2) if cac > 0 else None,
        }
