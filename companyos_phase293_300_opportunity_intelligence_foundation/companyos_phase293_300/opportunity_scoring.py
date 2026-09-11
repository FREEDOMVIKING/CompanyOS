class OpportunityScoring:
    WEIGHTS = {
        "demand": 0.22,
        "speed_to_revenue": 0.16,
        "margin": 0.14,
        "automation": 0.14,
        "competition_advantage": 0.12,
        "recurring_revenue": 0.12,
        "capital_efficiency": 0.10,
    }

    def score(self, metrics):
        total = 0.0
        for key, weight in self.WEIGHTS.items():
            value = max(0.0, min(10.0, float(metrics.get(key, 0))))
            total += value * weight
        return round(total, 3)
