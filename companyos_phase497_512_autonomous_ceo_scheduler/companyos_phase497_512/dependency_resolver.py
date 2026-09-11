class DependencyResolver:
    """499: resolve blocked mission dependencies from available evidence."""

    def resolve(self, mission, context):
        blockers = list(mission.get("blocked_on") or [])
        resolved = []

        for blocker in blockers:
            if blocker == "validation_evidence" and context.get("validation_metrics"):
                resolved.append(blocker)
            elif blocker == "operations_metrics" and context.get("operating_metrics"):
                resolved.append(blocker)

        mission = dict(mission)
        mission["blocked_on"] = [b for b in blockers if b not in resolved]
        return {"mission": mission, "resolved": resolved}
