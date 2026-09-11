class CustomerSuccessKPIs:
    """651: customer success KPI calculation."""

    def calculate(self, metrics):
        start=max(1,int(metrics.get("customers_start",0)))
        retained=int(metrics.get("customers_retained",0))
        expanded=float(metrics.get("expansion_revenue",0))
        churned=float(metrics.get("churned_revenue",0))
        starting_revenue=max(1.0,float(metrics.get("starting_recurring_revenue",0)))
        return {
            "logo_retention_rate":round(retained/start,4),
            "net_revenue_retention":round((starting_revenue-churned+expanded)/starting_revenue,4),
            "support_csat":float(metrics.get("support_csat",0)),
            "time_to_value_hours":float(metrics.get("time_to_value_hours",0)),
        }
