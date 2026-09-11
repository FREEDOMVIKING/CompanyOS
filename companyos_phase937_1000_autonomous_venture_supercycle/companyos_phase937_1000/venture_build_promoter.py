class VentureBuildPromoter:
    """961-964: create build-stage venture mission on GO."""
    def promote(self, validation_mission, validation):
        if validation.get("decision") != "GO":
            return None
        ctx = dict((validation_mission or {}).get("context") or {})
        sid = validation_mission.get("mission_id","validation")
        return {
            "mission_id": f"{sid}_build",
            "mission_type": "build",
            "priority": 0.98,
            "attempts": 0,
            "blocked_on": [],
            "status": "queued",
            "context": {
                **ctx,
                "validation_result": validation,
                "venture_stage": "build",
                "objective": "build the smallest validated product with measurable customer value",
            }
        }
