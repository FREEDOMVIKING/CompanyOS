from companyos_phase513_528 import CEOQualityBridge
from .candidate_deduper import CandidateDeduper
from .candidate_priority import CandidatePriority
from .quality_mission_generator import QualityMissionGenerator
from .candidate_store import CandidateStore
from .decision_event_router import DecisionEventRouter
from .quality_portfolio_memory import QualityPortfolioMemory

class AutonomousQualityCycle:
    """541: evidence -> quality candidates -> routed missions."""

    def __init__(self, root):
        self.root = root
        self.quality = CEOQualityBridge(root)
        self.store = CandidateStore(root)
        self.memory = QualityPortfolioMemory(root)

    def run(self):
        result = self.quality.run()
        candidates = result.get("candidates",[])
        candidates = CandidateDeduper().unique(candidates)
        candidates = CandidatePriority().rank(candidates)
        self.store.save(candidates)

        missions = QualityMissionGenerator().generate(candidates)

        router = DecisionEventRouter()
        for candidate in candidates[:20]:
            self.memory.append(candidate, router.event_for(candidate))

        return {
            "success":True,
            "status":"autonomous_quality_cycle_completed",
            "candidate_count":len(candidates),
            "candidates":candidates,
            "generated_missions":missions,
        }
