class ProviderResultBridge:
    """794: normalize runtime provider result maps from mission context."""

    def build(self, mission, execution_result=None):
        context = dict((mission or {}).get("context") or {})
        provider_results = dict(context.get("provider_results") or {})

        if execution_result and isinstance(execution_result, dict):
            data = execution_result.get("data") or {}
            if isinstance(data, dict) and isinstance(data.get("provider_results"), dict):
                provider_results.update(data["provider_results"])

        return {"provider_results": provider_results}
