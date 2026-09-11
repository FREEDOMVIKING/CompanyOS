class ReleasePlanner:
    def plan(self, release):
        environment=release.get("environment","staging")
        return {
            "release":release,
            "steps":["preflight","deploy","smoke_test","monitor","rollback_if_needed"],
            "requires_approval":environment=="production"
        }
