class OperatingKPIs:
    """566: derive core operating metrics."""

    def calculate(self, metrics):
        visitors=max(1,int(metrics.get("qualified_visitors",0)))
        activated=int(metrics.get("activated_users",0))
        paying=int(metrics.get("paying_customers",0))
        retained=int(metrics.get("retained_customers",0))
        start=max(1,int(metrics.get("customers_start",0)))
        return {
            "activation_rate":round(activated/visitors,4),
            "paid_conversion_rate":round(paying/max(1,activated),4),
            "retention_rate":round(retained/start,4),
            "mrr":float(metrics.get("mrr",0)),
            "gross_margin":float(metrics.get("gross_margin",0)),
        }
