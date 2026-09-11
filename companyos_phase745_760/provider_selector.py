from .provider_health import ProviderHealth
class ProviderSelector:
    """746: select healthiest available provider."""
    def choose(self, providers):
        scored = []
        for p in providers or []:
            item = dict(p)
            item["health_score"] = ProviderHealth().score(item)
            scored.append(item)
        scored.sort(key=lambda x: x["health_score"], reverse=True)
        return {"selected": scored[0] if scored else None, "ranked": scored}
