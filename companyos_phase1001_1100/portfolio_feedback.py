class PortfolioFeedback:
    """1077-1084: send venture outcomes back to CEO portfolio strategy."""
    def summarize(self, venture_id, launch_health, revenue, growth, incidents):
        return {
            "venture_id":venture_id,
            "operational_health":launch_health.get("status"),
            "net_revenue":revenue.get("net_revenue",0),
            "growth_score":growth.get("growth_score",0),
            "incident_count":len(incidents.get("incidents",[])),
            "portfolio_action":(
                "scale_cautiously"
                if launch_health.get("healthy") and growth.get("growth_score",0)>=0.5
                else "optimize_before_scaling"
            )
        }
