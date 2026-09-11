class IntegrationReport:
    """735: concise integration report."""

    def build(self, result):
        return {
            "success":bool(result.get("success")),
            "status":result.get("status"),
            "assertions":result.get("assertions"),
            "recovery":result.get("recovery"),
            "cycle_probe":result.get("cycle_probe"),
            "venture_stage":(result.get("venture") or {}).get("stage"),
            "queue_count":(result.get("queue") or {}).get("count"),
        }
