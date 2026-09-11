class TriggerRouter:
    ROUTES = {
        "market_signal":"research",
        "customer_issue":"customer_success",
        "build_ready":"product",
        "deployment_ready":"operations",
        "revenue_signal":"growth",
        "finance_signal":"finance",
        "health_alert":"operations"
    }

    def route(self, event):
        return {
            "event": event,
            "department": self.ROUTES.get(event.get("kind"), "operations")
        }
