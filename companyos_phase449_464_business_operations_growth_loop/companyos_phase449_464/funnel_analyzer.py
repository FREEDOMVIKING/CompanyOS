class FunnelAnalyzer:
    """454: basic acquisition/activation funnel analysis."""

    def analyze(self, metrics):
        visitors = max(1, int(metrics.get("qualified_visitors",0)))
        leads = int(metrics.get("leads",0))
        activated = int(metrics.get("activated_users",0))
        paid = int(metrics.get("paying_customers",0))
        return {
            "lead_conversion":round(leads/visitors,4),
            "activation_rate":round(activated/max(1,leads),4),
            "trial_to_paid":round(paid/max(1,activated),4),
        }
