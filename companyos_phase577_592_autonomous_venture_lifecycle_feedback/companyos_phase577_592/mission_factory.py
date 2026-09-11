import hashlib

class MissionFactory:
    """583: create deterministic next missions from venture lifecycle state."""

    TYPE_MAP = {
        "collect_targeted_evidence":"research",
        "run_validation":"validation",
        "continue_bounded_build":"build",
        "prepare_controlled_launch":"operations",
        "repair_operational_issues":"operations",
        "measure_and_iterate":"operations",
        "portfolio_scale_review":"portfolio",
    }

    def build(self, venture_id, next_action, context):
        mission_type = self.TYPE_MAP.get(next_action, "research")
        raw = f"{venture_id}:{next_action}"
        return {
            "mission_id":"mission_" + hashlib.sha256(raw.encode()).hexdigest()[:12],
            "mission_type":mission_type,
            "priority":0.95 if mission_type in ("validation","build") else 0.8,
            "attempts":0,
            "blocked_on":[],
            "context":{**dict(context or {}), "venture_id":venture_id, "next_action":next_action},
        }
