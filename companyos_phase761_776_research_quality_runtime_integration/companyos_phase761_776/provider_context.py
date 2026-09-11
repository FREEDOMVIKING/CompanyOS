class ProviderContext:
    """761: normalize provider status for live research execution."""
    def build(self, mission):
        ctx=dict((mission or {}).get("context") or {})
        return {
            "current_provider":ctx.get("provider_hint") or "github",
            "query_type":ctx.get("query_type") or "market",
            "attempts":int((mission or {}).get("attempts",0)),
        }
