from .rate_limit_detector import RateLimitDetector
class RetryClassifier:
    TRANSIENT=("timeout","temporarily unavailable","connection reset","service unavailable")
    def classify(self,result):
        if RateLimitDetector().detect(result)["rate_limited"]:
            return {"retryable":True,"reason":"provider_rate_limited","hard_failure":False}
        text=str(result or "").lower()
        if any(x in text for x in self.TRANSIENT):
            return {"retryable":True,"reason":"transient_provider_error","hard_failure":False}
        success=bool(result.get("success")) if isinstance(result,dict) else False
        return {"retryable":False,"reason":"success" if success else "execution_failed","hard_failure":not success}
