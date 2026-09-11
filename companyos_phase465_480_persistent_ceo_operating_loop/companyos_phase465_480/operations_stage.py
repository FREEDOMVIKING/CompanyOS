from companyos_phase449_464 import CEOOperationsBridge

class OperationsStage:
    """474: run measured operating review when metrics are available."""

    def __init__(self):
        self.bridge = CEOOperationsBridge()

    def run(self, context=None):
        context = context or {}
        metrics = context.get("operating_metrics")

        if not metrics:
            return {
                "success":True,
                "status":"operations_waiting_for_metrics",
                "stage":"operations",
                "data":{"decision":"hold_for_more_evidence"},
            }

        review = self.bridge.operating_review(metrics)
        decision = (review.get("portfolio_decision") or {}).get("decision")
        return {
            "success":True,
            "status":"operations_review_ready",
            "stage":"operations",
            "data":{"review":review,"decision":decision},
        }
