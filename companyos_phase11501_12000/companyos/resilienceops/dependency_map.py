class DependencyMap:
    def build(self, services):
        return {
            s.get("name"): list(s.get("depends_on", []))
            for s in (services or [])
        }
