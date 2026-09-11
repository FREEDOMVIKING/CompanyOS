class RevenueTelemetry:
    """1037-1044: basic revenue and unit-economics telemetry."""
    def compute(self, revenue=0, customers=0, spend=0, refunds=0):
        net=float(revenue)-float(refunds)
        cac=(float(spend)/customers) if customers else 0.0
        arpu=(net/customers) if customers else 0.0
        return {
            "gross_revenue":float(revenue),
            "net_revenue":round(net,2),
            "customers":int(customers),
            "cac":round(cac,2),
            "arpu":round(arpu,2),
            "refunds":float(refunds),
        }
