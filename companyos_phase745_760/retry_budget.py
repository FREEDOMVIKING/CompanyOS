class RetryBudget:
    """756: provider-specific bounded retry budgets."""
    LIMITS={"github":2,"hacker_news":3,"public_web":4,"official_sources":3,"local_cache":1}
    def remaining(self, provider, attempts):
        limit=self.LIMITS.get(provider,2)
        return max(0,limit-int(attempts))
