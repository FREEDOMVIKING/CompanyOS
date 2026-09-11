class FinancialSnapshot:
    """657: normalize venture financial inputs."""

    def build(self, metrics):
        return {
            "revenue": float(metrics.get("revenue",0)),
            "mrr": float(metrics.get("mrr",0)),
            "variable_costs": float(metrics.get("variable_costs",0)),
            "fixed_costs": float(metrics.get("fixed_costs",0)),
            "cash_available": float(metrics.get("cash_available",0)),
            "acquisition_spend": float(metrics.get("acquisition_spend",0)),
            "paying_customers": int(metrics.get("paying_customers",0)),
            "gross_margin_rate": float(metrics.get("gross_margin_rate",0)),
            "monthly_churn_rate": float(metrics.get("monthly_churn_rate",0)),
        }
