class CampaignPlan:
    """629: create measurable launch/growth campaign plan."""

    def build(self, positioning, channels):
        return {
            "objective":"generate qualified commercial evidence",
            "positioning":positioning,
            "channels":channels[:3],
            "assets":[
                "landing_page_or_offer_page",
                "clear_call_to_action",
                "proof_or_demo_asset",
                "measurement_instrumentation",
            ],
            "success_metrics":["qualified_leads","activations","paying_customers","retained_customers"],
            "automatic_paid_spend":False,
        }
