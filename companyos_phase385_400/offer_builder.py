class OfferBuilder:
    """389: create a lightweight test offer."""

    def build(self, thesis):
        model = thesis.get("business_model") or {}
        return {
            "offer_name": thesis.get("name"),
            "customer": thesis.get("customer"),
            "outcome": thesis.get("core_problem"),
            "pricing_model": model.get("primary") if isinstance(model, dict) else str(model),
            "delivery_mode": "manual_or_concierge_first",
            "requires_full_product": False,
        }
