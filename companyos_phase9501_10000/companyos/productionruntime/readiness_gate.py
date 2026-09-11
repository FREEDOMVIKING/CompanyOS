class ProductionReadinessGate:
    def evaluate(self, preflight, observability, approval_summary):
        checks={
            "preflight":bool(preflight.get("passed")),
            "observability":bool(observability.get("healthy")),
            "approval_queue_operational":approval_summary is not None
        }
        return {"ready":all(checks.values()),"checks":checks}
