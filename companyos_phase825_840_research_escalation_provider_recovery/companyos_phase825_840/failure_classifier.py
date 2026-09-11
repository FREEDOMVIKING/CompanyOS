from companyos_phase737_744 import RateLimitDetector

class FailureClassifier:
    """825: classify provider failures into actionable categories."""

    def classify(self, result):
        text = str(result or "").lower()
        if RateLimitDetector().detect(result)["rate_limited"]:
            return {"kind":"rate_limited","retryable":True,"escalate":True}
        if "timeout" in text:
            return {"kind":"timeout","retryable":True,"escalate":True}
        if "not_configured" in text or "adapter_not_configured" in text:
            return {"kind":"not_configured","retryable":False,"escalate":True}
        if isinstance(result, dict) and result.get("success"):
            return {"kind":"none","retryable":False,"escalate":False}
        return {"kind":"provider_error","retryable":True,"escalate":True}
