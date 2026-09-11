from __future__ import annotations

class TimeToRevenue:
    """379: estimate validation and first-revenue horizon."""

    def estimate(self, startup):
        complexity = startup.get("complexity")
        if complexity == "medium":
            return {"validation_days":[7,21],"first_revenue_days":[21,60]}
        return {"validation_days":[3,14],"first_revenue_days":[14,45]}
