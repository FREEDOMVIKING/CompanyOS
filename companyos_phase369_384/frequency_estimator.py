from __future__ import annotations

class FrequencyEstimator:
    """374: estimate recurrence of the problem from evidence density."""

    def score(self, cluster):
        count = int(cluster.get("count", 0))
        return min(10, 2 + count)
