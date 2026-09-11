class PricingTest:
    """390: suggest initial pricing-test bands, not automatic charging."""

    def create(self, thesis):
        customer = str(thesis.get("customer","")).lower()
        if "business" in customer or "contractor" in customer or "team" in customer:
            bands = [29, 79, 199]
        else:
            bands = [9, 29, 79]
        return {
            "currency":"USD",
            "monthly_price_points": bands,
            "test_type":"stated_preference_or_checkout_intent",
            "automatic_charging": False,
        }
