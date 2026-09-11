from .candidate_router import CandidateRouter
from .research_more_mission import ResearchMoreMission
from .validation_candidate_builder import ValidationCandidateBuilder

class QualitySchedulerBridge:
    """533: translate quality decisions into scheduler-ready missions."""

    def build_mission(self, candidate):
        route = CandidateRouter().route(candidate)

        if route == "reject":
            return {
                "mission_type":"none",
                "status":"candidate_rejected",
                "candidate":candidate.get("name"),
            }

        if route == "research_more":
            return ResearchMoreMission().build(candidate)

        thesis = ValidationCandidateBuilder().build(candidate)
        priority = 1.0 if (candidate.get("decision") or {}).get("decision") == "priority_validate" else 0.9
        return {
            "mission_type":"validation",
            "priority":priority,
            "blocked_on":["validation_evidence"],
            "context":{"top_thesis":thesis,"thesis":thesis},
        }
