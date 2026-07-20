class RevenueExperimenter:
    """152: design bounded reversible revenue experiments."""
    def design(self, hypothesis, budget_limit=0):
        return {
            "hypothesis":hypothesis,
            "experiment":"bounded_offer_test",
            "budget_limit":max(0,float(budget_limit)),
            "reversible":True,
            "autonomous_inside_limit":True,
            "financial_action_taken":False,
        }
