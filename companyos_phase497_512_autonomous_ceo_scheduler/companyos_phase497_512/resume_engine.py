from .dependency_resolver import DependencyResolver

class ResumeEngine:
    """507: resume blocked missions when evidence dependencies resolve."""

    def resume(self, missions, context):
        resolver = DependencyResolver()
        resumed, still_blocked = [], []

        for mission in missions:
            result = resolver.resolve(mission, context)
            updated = result["mission"]
            if updated.get("blocked_on"):
                still_blocked.append(updated)
            else:
                resumed.append(updated)

        return {"resumed": resumed, "blocked": still_blocked}
