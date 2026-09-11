class BusinessCase:
    """561: convert a thesis/venture packet into an explicit business case."""

    def build(self, venture):
        brief = venture.get("brief") or {}
        return {
            "venture_id": venture.get("venture_id"),
            "product_name": brief.get("product_name") or venture.get("name"),
            "target_customer": brief.get("target_customer"),
            "problem": brief.get("problem"),
            "business_model": brief.get("business_model"),
            "stage": venture.get("stage","incubating"),
            "assumptions": [
                "customer pain is real",
                "solution produces measurable value",
                "acquisition can be repeated economically",
            ],
        }
