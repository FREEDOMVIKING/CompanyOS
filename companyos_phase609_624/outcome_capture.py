class OutcomeCapture:
    """620: normalize post-delivery measured outcomes."""

    def capture(self, payload):
        return {
            "deployment_success": bool(payload.get("deployment_success")),
            "activation_rate": float(payload.get("activation_rate",0)),
            "retention_rate": float(payload.get("retention_rate",0)),
            "revenue_signal": float(payload.get("revenue_signal",0)),
            "error_rate": float(payload.get("error_rate",0)),
            "customer_feedback_count": int(payload.get("customer_feedback_count",0)),
        }
