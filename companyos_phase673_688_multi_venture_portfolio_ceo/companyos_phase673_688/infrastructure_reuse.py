class InfrastructureReuse:
    """678: detect shared infrastructure opportunities."""

    COMPONENTS = (
        "auth","billing","telemetry","email","crm","analytics",
        "deployment","database","support","logging"
    )

    def recommend(self, ventures):
        usage = {c:[] for c in self.COMPONENTS}
        for v in ventures:
            needs = set(v.get("infrastructure_needs",[]))
            for c in self.COMPONENTS:
                if c in needs:
                    usage[c].append(v.get("venture_id"))
        return {
            "shared_candidates":{
                c:ids for c,ids in usage.items() if len(ids) >= 2
            }
        }
