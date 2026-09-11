from companyos_phase857_872 import CEORevalidationRuntimeBridge
from .provider_task_router import ProviderTaskRouter
from .task_executor import RevalidationTaskExecutor
from .task_result_normalizer import TaskResultNormalizer
from .round_evidence_store import RoundEvidenceStore
from .evidence_feedback_bridge import EvidenceFeedbackBridge
from .validation_rerunner import ValidationRerunner
from .convergence_tracker import ConvergenceTracker
from .decision_convergence import DecisionConvergence
from .bounded_round_policy import BoundedRoundPolicy
from .human_review_gate import HumanReviewGate
from .venture_archive_bridge import VentureArchiveBridge
from .build_handoff_bridge import BuildHandoffBridge
from .convergence_audit import ConvergenceAudit

class ClosedLoopRevalidationController:
    """886: execute REVISE missions until bounded convergence."""
    def __init__(self,root):
        self.root=root
        self.store=RoundEvidenceStore(root)
        self.audit=ConvergenceAudit(root)

    def run_round(self,validation_mission,validation_result,provider_results=None,history=None,round_no=1,max_rounds=3):
        policy=BoundedRoundPolicy().evaluate(round_no,max_rounds)
        if not policy["allowed"]:
            conf=float((validation_result.get("scores") or {}).get("validation_confidence",0))
            return {"success":True,"status":"revalidation_round_limit_reached","decision":"EXHAUSTED",
                    "archive":VentureArchiveBridge().build("EXHAUSTED",conf)}

        plan=CEORevalidationRuntimeBridge(self.root).run(validation_mission,validation_result,history=history)
        tasks=[ProviderTaskRouter().route(t) for t in plan.get("tasks",[])]
        executions=[RevalidationTaskExecutor().execute(t,provider_results or {}) for t in tasks]
        new_evidence=TaskResultNormalizer().normalize(executions)
        self.store.save(validation_mission.get("mission_id"),round_no,new_evidence)

        updated=EvidenceFeedbackBridge().apply(validation_mission,new_evidence)
        rerun=ValidationRerunner(self.root).run(updated)
        new_history=ConvergenceTracker().append(history,rerun)
        convergence=DecisionConvergence().evaluate(new_history)
        conf=float((rerun.get("scores") or {}).get("validation_confidence",0))
        review=HumanReviewGate().evaluate(convergence,conf)
        archive=VentureArchiveBridge().build(rerun.get("decision"),conf)
        build=BuildHandoffBridge().build(updated,rerun) if rerun.get("decision")=="GO" else None

        result={"success":True,"status":"closed_loop_revalidation_round_complete","round":round_no,
                "new_evidence_count":len(new_evidence),"validation":rerun,"history":new_history,
                "convergence":convergence,"human_review":review,"archive":archive,"next_mission":build}
        self.audit.append(result)
        return result
