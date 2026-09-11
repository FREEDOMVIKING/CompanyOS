class FailureClassifier:
    def classify(self, job, result):
        if not result:
            return {"kind":"missing_result","recoverable":True}
        if result.get("success"):
            return {"kind":"none","recoverable":False}
        err = str(result.get("error") or result.get("reason") or "").lower()
        if "capability" in err or "unsupported" in err:
            return {"kind":"capability_gap","recoverable":True}
        if "timeout" in err:
            return {"kind":"timeout","recoverable":True}
        if "approval" in err:
            return {"kind":"approval_required","recoverable":False}
        return {"kind":"execution_failure","recoverable":True}
