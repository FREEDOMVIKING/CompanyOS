class ContinuityPlanner:
    def plan(self, critical_services):
        return [{
            "service":s.get("name"),
            "rto_minutes":int(s.get("rto_minutes",60)),
            "rpo_minutes":int(s.get("rpo_minutes",15)),
            "fallback":s.get("fallback","manual_safe_mode")
        } for s in (critical_services or [])]
