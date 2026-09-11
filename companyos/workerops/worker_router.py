class WorkerRouter:
    ROUTES={
        "daily_health":"operations",
        "market_scan":"research",
        "portfolio_review":"finance",
        "event_task":"operations",
        "research":"research",
        "build":"product",
        "growth":"growth",
        "finance":"finance",
        "customer_success":"customer_success",
        "deploy":"operations"
    }
    def route(self, job):
        payload=job.get("payload",{})
        dept=payload.get("department")
        return dept or self.ROUTES.get(job.get("kind"),"operations")
