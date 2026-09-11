class DeliveryFeedback:
    """621: convert delivery outcomes into lifecycle feedback."""

    def build(self, outcome):
        return {
            "mission_success": bool(outcome.get("deployment_success")),
            "activation_rate": outcome.get("activation_rate",0),
            "retention_rate": outcome.get("retention_rate",0),
            "revenue_signal": outcome.get("revenue_signal",0),
            "critical_issues": 1 if float(outcome.get("error_rate",0)) > 0.05 else 0,
            "notes": f"customer_feedback_count={outcome.get('customer_feedback_count',0)}",
        }
