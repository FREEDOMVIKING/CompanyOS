class RateLimitDetector:
    MARKERS=("http error 403","rate limit exceeded","too many requests","http 429","429 too many requests","secondary rate limit")
    def detect(self,result):
        text=str(result or "").lower()
        matched=[m for m in self.MARKERS if m in text]
        return {"rate_limited":bool(matched),"markers":matched}
