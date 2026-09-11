from companyos_phase737_744 import RateLimitDetector
class ProviderErrorNormalizer:
    """783: normalize provider errors for failover policy."""
    def normalize(self, result):
        text=str(result or "").lower()
        if RateLimitDetector().detect(result)["rate_limited"]:
            kind="rate_limited"
        elif "timeout" in text:
            kind="timeout"
        elif "not_configured" in text:
            kind="not_configured"
        elif result.get("success"):
            kind="none"
        else:
            kind="provider_error"
        return {"kind":kind,"retryable":kind in ("rate_limited","timeout","provider_error","not_configured")}
