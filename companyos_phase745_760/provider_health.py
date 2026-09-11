class ProviderHealth:
    """745: score provider health from availability, failures, and cooldown state."""
    def score(self, provider):
        availability = float(provider.get("availability", 1.0))
        recent_failures = int(provider.get("recent_failures", 0))
        cooldown = bool(provider.get("cooldown_active", False))
        latency = float(provider.get("latency_ms", 0))
        score = availability * 10
        score -= min(5, recent_failures * 1.5)
        if cooldown:
            score -= 5
        if latency > 3000:
            score -= 1
        return round(max(0.0, min(10.0, score)), 2)
