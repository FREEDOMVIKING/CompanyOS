class FallbackEngine:
    def choose(self, ranked_connectors, attempted=None):
        attempted=set(attempted or [])
        for c in ranked_connectors or []:
            if c.get("name") not in attempted and c.get("enabled",True):
                return {"selected":c.get("name"),"reason":"highest_healthy_available"}
        return {"selected":None,"reason":"no_available_connector"}
