class HypothesisUpdater:
    """595: revise hypotheses based on observed evidence."""

    def update(self, hypotheses, lessons):
        h = dict(hypotheses or {})
        h.setdefault("customer_problem_valid", None)
        h.setdefault("solution_value_valid", None)
        h.setdefault("willingness_to_pay_valid", None)

        if "weak_activation" in lessons:
            h["solution_value_valid"] = False
        if "weak_retention" in lessons:
            h["customer_problem_valid"] = False
        if "no_revenue_signal" in lessons:
            h["willingness_to_pay_valid"] = False
        if any(x.startswith("stage_advanced:") for x in lessons):
            if h["customer_problem_valid"] is None:
                h["customer_problem_valid"] = True
        return h
