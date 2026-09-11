class DemandThresholds:
    """391: configurable go/no-go evidence thresholds."""

    def defaults(self):
        return {
            "landing_page_visit_min": 100,
            "email_conversion_min": 0.08,
            "interview_count_min": 5,
            "pain_confirm_rate_min": 0.60,
            "willingness_to_pay_confirm_rate_min": 0.30,
            "qualified_leads_min": 5,
        }
