class GrowthDecision:
    """636: evidence-based growth action."""

    def decide(self, acquisition_score, revenue_signal, economics, vanity):
        if vanity.get("vanity_only"):
            action="do_not_scale_research_message_or_channel"
        elif revenue_signal >= 6 and acquisition_score >= 5 and economics.get("economics_positive"):
            action="prepare_scale_review"
        elif revenue_signal >= 2 or acquisition_score >= 3:
            action="iterate_growth_experiment"
        else:
            action="revalidate_offer_positioning_or_channel"
        return {
            "decision":action,
            "automatic_financial_commitment":False,
        }
