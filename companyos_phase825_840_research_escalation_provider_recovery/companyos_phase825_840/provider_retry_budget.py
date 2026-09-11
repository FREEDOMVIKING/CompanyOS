class ProviderRetryBudget:
    """829: bounded retry budgets by provider class."""

    LIMITS = {
        "github": 2,
        "public_web": 4,
        "hacker_news": 3,
        "official_sources": 3,
        "local_cache": 1,
    }

    def remaining(self, provider, attempts):
        return max(0, self.LIMITS.get(provider, 2) - int(attempts))
