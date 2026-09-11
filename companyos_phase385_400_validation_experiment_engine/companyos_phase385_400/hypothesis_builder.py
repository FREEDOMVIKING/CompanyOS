class HypothesisBuilder:
    """385: turn a market thesis into falsifiable validation hypotheses."""

    def build(self, thesis):
        return {
            "customer_hypothesis": thesis.get("customer"),
            "problem_hypothesis": thesis.get("core_problem"),
            "value_hypothesis": f"Target customers will value a solution for: {thesis.get('core_problem')}",
            "willingness_to_pay_hypothesis": thesis.get("business_model"),
            "success_condition": "measurable demand and willingness-to-pay evidence exceeds thresholds",
        }
