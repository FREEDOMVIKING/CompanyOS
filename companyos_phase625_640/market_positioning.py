class MarketPositioning:
    """625: explicit customer/problem/value positioning."""

    def build(self, venture):
        brief = venture.get("brief") or {}
        return {
            "product_name": brief.get("product_name") or venture.get("name"),
            "target_customer": brief.get("target_customer"),
            "problem": brief.get("problem"),
            "value_proposition": brief.get("value_proposition") or "measurably improve the target workflow",
            "positioning_test_required": True,
        }
