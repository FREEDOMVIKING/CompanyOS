class KPIContract:
    """411: business/product KPIs every venture must instrument."""

    def build(self):
        return {
            "acquisition":["qualified_visitors","lead_conversion"],
            "activation":["activation_rate","time_to_first_value"],
            "value":["successful_core_outcomes","outcome_success_rate"],
            "retention":["return_rate","retained_accounts"],
            "revenue":["trial_to_paid","mrr","gross_margin"],
            "quality":["error_rate","support_incidents"],
        }
