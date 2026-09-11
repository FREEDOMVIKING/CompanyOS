class ProviderAdapter:
    """777: normalized provider adapter contract."""
    def execute(self, provider, query, context=None):
        context = context or {}
        mock = context.get("provider_results", {}).get(provider)
        if mock is None:
            return {
                "success": False,
                "provider": provider,
                "error": "provider_adapter_not_configured",
                "items": [],
            }
        if isinstance(mock, Exception):
            return {
                "success": False,
                "provider": provider,
                "error": str(mock),
                "items": [],
            }
        return {
            "success": bool(mock.get("success", True)),
            "provider": provider,
            "items": mock.get("items", []),
            "error": mock.get("error"),
        }
