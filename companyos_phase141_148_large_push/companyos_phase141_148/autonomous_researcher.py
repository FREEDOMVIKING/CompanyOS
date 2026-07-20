from __future__ import annotations
from typing import Any, Dict, List

class AutonomousResearcher:
    """141: continuously identify knowledge gaps and generate research missions."""

    def create_missions(self, goals: List[Dict[str, Any]], evidence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        known = {str(x.get("topic")) for x in evidence if x.get("topic")}
        missions = []
        for goal in goals:
            for topic in goal.get("required_topics", []):
                if str(topic) not in known:
                    missions.append({
                        "topic": str(topic),
                        "objective": f"research_and_validate:{topic}",
                        "autonomous": True,
                        "status": "queued",
                    })
        return missions
