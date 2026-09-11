import hashlib
from .quality_scheduler_bridge import QualitySchedulerBridge

class QualityMissionGenerator:
    """534: generate deduplicated mission envelopes from candidate decisions."""

    def generate(self, candidates):
        out = []
        bridge = QualitySchedulerBridge()
        for c in candidates:
            mission = bridge.build_mission(c)
            if mission.get("mission_type") == "none":
                continue
            key = f"{mission.get('mission_type')}:{c.get('name')}:{c.get('theme')}"
            mission["mission_id"] = "mission_" + hashlib.sha256(key.encode()).hexdigest()[:12]
            mission["attempts"] = 0
            mission["candidate_quality_score"] = c.get("quality_score",0)
            out.append(mission)
        return out
