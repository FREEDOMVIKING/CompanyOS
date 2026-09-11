class RevenueAnalyzer:
    """456: revenue growth summary."""

    def analyze(self, metrics):
        current = float(metrics.get("mrr",0))
        previous = float(metrics.get("previous_mrr",0))
        growth = 0.0 if previous <= 0 else (current-previous)/previous
        return {
            "mrr":current,
            "previous_mrr":previous,
            "mrr_growth_rate":round(growth,4),
        }
