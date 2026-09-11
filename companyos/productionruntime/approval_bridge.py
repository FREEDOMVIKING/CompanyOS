class ProductionApprovalBridge:
    def summarize(self, queue):
        queue=list(queue or [])
        return {
            "pending_count":sum(1 for x in queue if x.get("status")=="pending"),
            "approved_count":sum(1 for x in queue if x.get("status")=="approved"),
            "denied_count":sum(1 for x in queue if x.get("status")=="denied"),
            "blocked_until_decision":[x for x in queue if x.get("status")=="pending"]
        }
