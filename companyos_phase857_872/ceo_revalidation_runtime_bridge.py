from .gap_analyzer import ValidationGapAnalyzer
from .revalidation_mission_generator import RevalidationMissionGenerator
from .evidence_acquisition_planner import EvidenceAcquisitionPlanner
from .hypothesis_research_tasks import HypothesisResearchTasks
from .contradiction_resolution import ContradictionResolutionTasks
from .provider_revalidation_router import ProviderRevalidationRouter
from .confidence_delta import ConfidenceDeltaTracker
from .stagnation_detector import StagnationDetector
from .bounded_loop import BoundedRevalidationLoop
from .decision_escalator import DecisionEscalator
from .revalidation_journal import RevalidationJournal

class CEORevalidationRuntimeBridge:
    def __init__(self,root): self.journal=RevalidationJournal(root)
    def run(self,source_mission,validation,history=None,provider_health=None):
        attempt=int((validation.get("revalidation") or {}).get("next_attempt",source_mission.get("attempts",0)+1))
        gaps=ValidationGapAnalyzer().analyze(validation)
        plans=EvidenceAcquisitionPlanner().plan(gaps)
        tasks=HypothesisResearchTasks().build(plans)
        topics=(validation.get("contradictions") or {}).get("topics",[])
        tasks += ContradictionResolutionTasks().build(topics)
        routed=[ProviderRevalidationRouter().route(t,provider_health) for t in tasks]
        mission=RevalidationMissionGenerator().generate(source_mission,gaps,attempt)
        mission["context"]["research_tasks"]=routed

        hist=list(history or [])
        current=float((validation.get("scores") or {}).get("validation_confidence",0))
        before=float(hist[-1].get("confidence",current)) if hist else current
        delta=ConfidenceDeltaTracker().calculate(before,current)
        deltas=[x.get("delta",x) if isinstance(x,dict) else x for x in []]
        delta_rows=[{"delta":float(x.get("delta",0))} for x in hist[-2:] if isinstance(x,dict) and "delta" in x]
        delta_rows.append(delta)
        stagnant=StagnationDetector().evaluate(delta_rows)
        decision=validation.get("decision","REVISE")
        loop=BoundedRevalidationLoop().evaluate(attempt,decision,stagnant["stagnant"])
        escalation=DecisionEscalator().resolve(decision,loop,current)
        result={"success":True,"status":"autonomous_revalidation_planned","attempt":attempt,"gaps":gaps,
                "tasks":routed,"revalidation_mission":mission,"confidence_delta":delta,
                "stagnation":stagnant,"loop":loop,"escalation":escalation}
        self.journal.append(result)
        return result
