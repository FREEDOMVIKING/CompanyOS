class GrowthExperiment:
    """453: create bounded growth experiments."""

    def design(self, hypothesis, channel, metric):
        return {
            "hypothesis":hypothesis,
            "channel":channel,
            "primary_metric":metric,
            "duration_days":14,
            "budget_class":"bounded",
            "success_rule":"predefined_metric_threshold_required",
            "automatic_external_spend":False,
        }
