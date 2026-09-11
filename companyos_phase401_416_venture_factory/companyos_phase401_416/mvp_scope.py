class MVPScope:
    """403: constrain the first product to the smallest testable value loop."""

    def define(self, brief):
        return {
            "must_have": [
                "single primary customer workflow",
                "core value-producing action",
                "basic onboarding",
                "result/output delivery",
                "usage and outcome instrumentation",
            ],
            "defer": [
                "broad platform features",
                "complex enterprise controls",
                "premature scaling",
                "nonessential integrations",
            ],
            "scope_rule": "smallest_product_that_can_test_value_and_retention",
        }
