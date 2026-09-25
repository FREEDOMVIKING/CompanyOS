class WorkerRouter:
    ROUTES = {
        "daily_health": "operations",
        "market_scan": "research",
        "portfolio_review": "finance",
        "event_task": "operations",
        "research": "research",
        "build": "product",
        "growth": "growth",
        "finance": "finance",
        "customer_success": "customer_success",
        "deploy": "operations"
    }

    def route(self, job):
        payload = job.get("payload", {})
        department = payload.get("department")
        if department:
            return department
        kind = job.get("kind")
        return self.ROUTES.get(kind, "operations")
