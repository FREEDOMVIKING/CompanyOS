from .provider_adapter import ProviderAdapter
class ProviderDispatcher:
    """778: dispatch normalized provider execution."""
    def dispatch(self, provider, query, context=None):
        return ProviderAdapter().execute(provider, query, context or {})
