class ValidationPlan:
    def create(self, opportunity):
        return {
            "opportunity": opportunity.get("name", "unnamed"),
            "steps": [
                "define falsifiable customer/problem hypothesis",
                "collect demand evidence",
                "identify current alternatives and competitor pricing",
                "test willingness-to-pay with lightweight offer or landing page",
                "estimate acquisition cost and gross margin",
                "set explicit go/no-go thresholds",
            ],
            "build_full_product_before_validation": False,
        }
