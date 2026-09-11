class ResearchProviderAdapter:
    name="research_provider"
    capabilities=["research","news"]
    live_supported=False

    def execute(self, request, timeout=30, live=False):
        return {
            "success":True,
            "simulated":not live,
            "adapter":self.name,
            "query":request.get("query"),
            "items":request.get("seed_items",[])
        }
