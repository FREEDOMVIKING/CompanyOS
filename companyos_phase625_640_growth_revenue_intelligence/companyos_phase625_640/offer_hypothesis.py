class OfferHypothesis:
    """626: testable commercial offer hypothesis."""

    def build(self, positioning):
        return {
            "customer": positioning.get("target_customer"),
            "promise": positioning.get("value_proposition"),
            "offer_type": "bounded_trial_or_pilot",
            "success_signal": "qualified_customer_conversion",
            "assumption": "customer perceives enough value to take a meaningful commercial action",
        }
