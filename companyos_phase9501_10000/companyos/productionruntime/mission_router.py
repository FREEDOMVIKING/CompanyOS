class MissionRouter:
    ROUTES={
        "research":"research",
        "validation":"research",
        "build":"product",
        "launch":"operations",
        "operate":"operations",
        "growth":"growth",
        "finance":"finance",
        "customer_success":"customer_success"
    }

    def route(self, mission):
        mtype=mission.get("mission_type","operate")
        return {
            **mission,
            "department":self.ROUTES.get(mtype,"operations")
        }
