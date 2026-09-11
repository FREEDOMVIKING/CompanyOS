class TelemetryContract:
    """619: required product/business events."""

    def build(self, kpis=None):
        kpis = kpis or {}
        events = [
            "product.signup",
            "product.activation",
            "product.core_value_completed",
            "product.error",
            "product.feedback_submitted",
        ]
        for category, metrics in kpis.items():
            for metric in metrics:
                events.append(f"{category}.{metric}")
        return {"required_events":list(dict.fromkeys(events))}
