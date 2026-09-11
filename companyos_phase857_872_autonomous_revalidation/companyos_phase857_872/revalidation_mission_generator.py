class RevalidationMissionGenerator:
    def generate(self, source_mission, gaps, attempt):
        sid=source_mission.get("mission_id","validation")
        return {"mission_id":f"{sid}_revalidate_{attempt}","mission_type":"research","priority":0.95,
                "attempts":attempt,"blocked_on":[],"status":"queued",
                "context":{"venture_id":(source_mission.get("context") or {}).get("venture_id"),
                           "revalidation":True,"validation_gaps":gaps,
                           "objective":"collect targeted evidence to resolve validation gaps"}}
