class ResearchExecutionPolicy:
    """765: decide advance, retry, fallback, or defer."""
    def decide(self, quality, provider_available=True, retry_remaining=1):
        if quality.get("passed"):
            return "advance"
        if not provider_available and retry_remaining>0:
            return "fallback"
        if retry_remaining>0:
            return "retry"
        return "defer"
