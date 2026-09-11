class ResearchMissionAdapter:
    """762: normalize CEO research mission inputs."""
    def adapt(self, mission):
        ctx=dict((mission or {}).get("context") or {})
        return {
            "mission_id":mission.get("mission_id"),
            "venture_id":ctx.get("venture_id") or (ctx.get("venture_record") or {}).get("venture_id"),
            "objective":ctx.get("objective") or ctx.get("next_action") or "collect targeted evidence",
            "query_type":ctx.get("query_type") or "market",
            "provider_hint":ctx.get("provider_hint") or "github",
            "attempts":int(mission.get("attempts",0)),
        }
