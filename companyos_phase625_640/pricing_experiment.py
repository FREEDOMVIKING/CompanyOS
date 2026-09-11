class PricingExperiment:
    """627: bounded pricing tests; does not transact or spend money."""

    def plan(self, baseline=None):
        baseline = float(baseline or 0)
        return {
            "experiment_type":"pricing_hypothesis",
            "variants":[
                {"name":"baseline","price":baseline},
                {"name":"value_test","price":round(baseline*1.25,2) if baseline else None},
            ],
            "measure":["qualified_conversion","trial_to_paid","retention","gross_margin"],
            "automatic_financial_action":False,
        }
