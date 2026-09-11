class RecurringOperations:
    """647: define recurring business-operating checks."""

    def schedule(self):
        return [
            {"task":"customer_health_review","cadence":"daily"},
            {"task":"support_backlog_review","cadence":"daily"},
            {"task":"service_quality_review","cadence":"daily"},
            {"task":"retention_and_churn_review","cadence":"weekly"},
            {"task":"feedback_theme_review","cadence":"weekly"},
            {"task":"operations_kpi_review","cadence":"weekly"},
        ]
