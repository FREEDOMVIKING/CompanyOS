class OutcomeClassifier:
    def classify(self, job, execution):
        job = job or {}
        execution = execution or {}

        payload = job.get("payload") or {}
        requires_approval = bool(
            payload.get("requires_approval")
            or job.get("requires_approval")
            or execution.get("requires_approval")
        )

        if execution.get("success") is True:
            return {
                "state": "completed",
                "resolved": True,
                "successful": True,
                "requires_approval": requires_approval
            }

        if execution.get("blocked") and (
            execution.get("reason") == "approval_required"
            or requires_approval
        ):
            return {
                "state": "deferred_for_approval",
                "resolved": True,
                "successful": False,
                "requires_approval": True
            }

        if execution.get("deduped") is True:
            return {
                "state": "deduplicated",
                "resolved": True,
                "successful": True,
                "requires_approval": requires_approval
            }

        if requires_approval and execution.get("success") is not True:
            return {
                "state": "deferred_for_approval",
                "resolved": True,
                "successful": False,
                "requires_approval": True
            }

        return {
            "state": "failed",
            "resolved": False,
            "successful": False,
            "requires_approval": requires_approval
        }
