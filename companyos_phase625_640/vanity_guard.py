class VanityGuard:
    """631: prevent impressions/clicks alone from being treated as business success."""

    def evaluate(self, metrics):
        meaningful = (
            int(metrics.get("qualified_leads",0)) > 0 or
            int(metrics.get("activated_users",0)) > 0 or
            int(metrics.get("paying_customers",0)) > 0 or
            float(metrics.get("revenue",0)) > 0
        )
        vanity_only = (
            int(metrics.get("impressions",0)) > 0 or int(metrics.get("clicks",0)) > 0
        ) and not meaningful
        return {
            "meaningful_business_signal":meaningful,
            "vanity_only":vanity_only,
            "success_allowed":meaningful and not vanity_only,
        }
