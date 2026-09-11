class UnitEconomics:
    """633: basic CAC/LTV/payback intelligence."""

    def calculate(self, metrics):
        spend=float(metrics.get("acquisition_spend",0))
        customers=int(metrics.get("paying_customers",0))
        arpa=float(metrics.get("average_revenue_per_account",0))
        margin=float(metrics.get("gross_margin_rate",0))
        monthly_churn=float(metrics.get("monthly_churn_rate",0))
        cac=spend/max(1,customers)
        ltv=(arpa*margin/max(monthly_churn,0.01)) if arpa and margin else 0.0
        return {
            "cac":round(cac,2),
            "estimated_ltv":round(ltv,2),
            "ltv_cac_ratio":round(ltv/max(cac,0.01),2) if ltv else 0.0,
            "economics_positive":bool(ltv and ltv > cac),
        }
