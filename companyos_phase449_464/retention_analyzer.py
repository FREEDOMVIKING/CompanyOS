class RetentionAnalyzer:
    """455: retention and churn summary."""

    def analyze(self, metrics):
        start = max(1, int(metrics.get("customers_start",0)))
        end = int(metrics.get("customers_end",0))
        churned = int(metrics.get("customers_churned",0))
        return {
            "gross_retention":round(max(0,end)/start,4),
            "churn_rate":round(churned/start,4),
        }
