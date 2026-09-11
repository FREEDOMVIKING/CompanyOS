class GrowthExperiment:
    """634: define one-variable-at-a-time growth experiments."""

    def build(self, hypothesis, metric, baseline=None):
        return {
            "hypothesis":hypothesis,
            "primary_metric":metric,
            "baseline":baseline,
            "change_one_major_variable":True,
            "stop_conditions":["critical_quality_issue","negative_customer_harm_signal"],
            "automatic_external_spend":False,
        }
