class ProviderResiliencePlanner:
    def plan(self, providers):
        healthy=[p for p in providers or [] if p.get("healthy")]
        ordered=sorted(healthy,key=lambda x:float(x.get("health_score",0)),reverse=True)
        return {
            "primary":ordered[0].get("name") if ordered else None,
            "fallbacks":[p.get("name") for p in ordered[1:]],
            "redundancy_ready":len(ordered)>=2
        }
