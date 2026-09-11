class FinancialHealth:
    """671: high-level financial sanity check."""

    def evaluate(self, review):
        anomalies=review.get("anomalies",{}).get("has_anomaly",False)
        runway=review.get("burn_runway",{}).get("runway_months")
        profitable=review.get("profitability",{}).get("profitable",False)
        healthy = profitable or (not anomalies and (runway is None or runway >= 6))
        return {
            "healthy":healthy,
            "profitable":profitable,
            "runway_months":runway,
            "has_anomaly":anomalies,
        }
