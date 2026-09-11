class PriorityEngine:
    """436: calculate venture priority from evidence and business state."""

    def score(self, venture):
        score = float(venture.get("priority", 0.5)) * 5
        metrics = venture.get("metrics") or {}
        score += min(2.0, float(metrics.get("validation_score", 0)) * 0.2)
        score += min(1.5, float(metrics.get("revenue_signal", 0)) * 0.15)
        score += min(1.0, float(metrics.get("retention_signal", 0)) * 0.10)
        score -= min(2.0, float(venture.get("failures", 0)) * 0.5)
        return round(max(0.0, min(10.0, score)), 3)
