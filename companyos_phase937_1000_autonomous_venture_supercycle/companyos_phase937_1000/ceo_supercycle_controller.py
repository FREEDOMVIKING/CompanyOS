from .evidence_rescore_engine import EvidenceRescoreEngine
from .adaptive_research_supervisor import AdaptiveResearchSupervisor
from .validation_convergence_engine import ValidationConvergenceEngine
from .venture_build_promoter import VentureBuildPromoter
from .mvp_scope_generator import MVPScopeGenerator
from .specialist_delegator import SpecialistDelegator
from .build_graph import BuildDependencyGraph
from .build_test_fix_loop import BuildTestFixLoop
from .release_candidate_gate import ReleaseCandidateGate
from .rollback_manager import RollbackManager
from .venture_lifecycle_store import VentureLifecycleStore
from .supercycle_audit import SupercycleAudit

class CEOSupercycleController:
    """998-999: unified research->validation->build supercycle orchestration."""
    def __init__(self,root):
        self.root=root
        self.state=VentureLifecycleStore(root)
        self.audit=SupercycleAudit(root)

    def run(self, validation_mission, validation_result, provider_results=None, max_research_rounds=3,
            build_result=None, test_results=None, safety_checks=None):
        ctx=dict((validation_mission or {}).get("context") or {})
        key=ctx.get("venture_id") or validation_mission.get("mission_id")

        packet=dict(ctx.get("research_packet") or {})
        rescored=EvidenceRescoreEngine().apply_to_validation(validation_result,packet)

        adaptive=None
        convergence=ValidationConvergenceEngine().decide(
            rescored, history=ctx.get("revalidation_history"), max_rounds_reached=False
        )

        if convergence["decision"]=="REVISE":
            adaptive=AdaptiveResearchSupervisor(self.root).run(
                validation_mission,rescored,provider_results or {},max_rounds=max_research_rounds
            )
            rescored=adaptive.get("final_validation",rescored)
            packet=dict(((adaptive.get("updated_mission") or {}).get("context") or {}).get("research_packet") or packet)
            rescored=EvidenceRescoreEngine().apply_to_validation(rescored,packet)

            hist=[]
            for r in adaptive.get("rounds",[]):
                v=r.get("validation") or {}
                hist.append({"confidence":float((v.get("scores") or {}).get("validation_confidence",0))})
            convergence=ValidationConvergenceEngine().decide(
                rescored, history=hist, max_rounds_reached=True
            )

        rescored["decision"]=convergence["decision"]
        rescored["decision_reason"]=convergence["reason"]

        build_mission=VentureBuildPromoter().promote(validation_mission,rescored)
        build_bundle=None

        if build_mission:
            scope=MVPScopeGenerator().generate(build_mission)
            specialists=SpecialistDelegator().assign(scope)
            graph=BuildDependencyGraph().build(specialists)
            loop=BuildTestFixLoop().run(build_result,test_results)
            rollback=RollbackManager().plan(artifact_ref="current_build",previous_ref="previous_build")
            rc=ReleaseCandidateGate().evaluate(loop,safety_checks,rollback["rollback_ready"])
            build_bundle={
                "mission":build_mission,
                "scope":scope,
                "specialists":specialists,
                "dependency_graph":graph,
                "build_loop":loop,
                "rollback":rollback,
                "release_candidate":rc,
            }

        stage="build" if build_mission else ("archive" if convergence["decision"]=="KILL" else "review")
        state={
            "stage":stage,
            "mission_id":validation_mission.get("mission_id"),
            "venture_id":key,
            "validation":rescored,
            "convergence":convergence,
            "build_bundle":build_bundle,
        }
        self.state.save(key,state)
        self.audit.append(state)

        return {
            "success":True,
            "status":"ceo_venture_supercycle_complete",
            "stage":stage,
            "rescored_validation":rescored,
            "adaptive_research":adaptive,
            "convergence":convergence,
            "build_bundle":build_bundle,
        }
