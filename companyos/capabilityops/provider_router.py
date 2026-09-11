class ProviderRouter:
    def choose(self, capability, providers):
        candidates=[
            p for p in (providers or [])
            if p.get("capability")==capability and p.get("enabled",True)
        ]
        candidates.sort(
            key=lambda p:(
                float(p.get("health_score",0)),
                -float(p.get("cost_score",0))
            ),
            reverse=True
        )
        return candidates[0] if candidates else None
