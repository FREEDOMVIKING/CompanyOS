class MetricInstrumentation:
    """424: translate KPI contract into implementation requirements."""

    def plan(self, kpis):
        events = []
        for category, metrics in kpis.items():
            for metric in metrics:
                events.append({
                    "category":category,
                    "metric":metric,
                    "event_name":f"{category}.{metric}",
                })
        return {"required_events":events, "event_count":len(events)}
