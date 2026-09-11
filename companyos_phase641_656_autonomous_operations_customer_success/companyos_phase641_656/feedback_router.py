class FeedbackRouter:
    """650: route feedback into product, support, growth, or strategy learning."""

    def route(self, item):
        category=item.get("category","general")
        mapping={
            "bug":"product_quality",
            "feature":"product_strategy",
            "support":"customer_success",
            "pricing":"growth_and_revenue",
            "positioning":"growth_and_revenue",
            "churn":"strategic_learning",
        }
        return {"destination":mapping.get(category,"strategic_learning"),"feedback":item}
