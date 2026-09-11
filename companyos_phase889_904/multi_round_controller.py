from companyos_phase873_888 import CEORevalidationExecutionBridge
from .round_scheduler import RevalidationRoundScheduler
from .round_state import RevalidationRoundState
from .history_store import RevalidationHistoryStore
from .diminishing_returns import DiminishingReturnsDetector
from .terminal_decision import TerminalDecisionResolver
from .build_dispatch import BuildDispatch
from .archive_dispatch import ArchiveDispatch
from .human_review_dispatch import HumanReviewDispatch
from .bounded_exhaustion import BoundedExhaustionPolicy
from .queue_handoff import QueueHandoff
from .orchestration_audit import OrchestrationAudit
from .mission_state_sync import MissionStateSync

class MultiRoundRevalidationController:
    """901: autonomously run REVISE -> evidence -> revalidate across bounded rounds."""
    def __init__(self,root):
        self.root=root
        self.executor=CEORevalidationExecutionBridge(root)
        self.state=RevalidationRoundState(root)
        self.history_store=RevalidationHistoryStore(root)
        self.audit=OrchestrationAudit(root)

    def run(self,validation_mission,validation_result,provider_results=None,max_rounds=3):
        key=(validation_mission.get("context") or {}).get("venture_id") or validation_mission.get("mission_id")
        history=list((validation_mission.get("context") or {}).get("revalidation_history") or [])
        current_validation=validation_result
        mission=validation_mission
        rounds=[]

        start_round=int((validation_mission.get("context") or {}).get("revalidation_round",0))+1

        for round_no in range(start_round,int(max_rounds)+1):
            sched=RevalidationRoundScheduler().next_round(round_no-1,current_validation.get("decision"),max_rounds)
            if not sched["run"]:
                break

            result=self.executor.run_round(
                mission,current_validation,provider_results or {},history=history,round_no=round_no,max_rounds=max_rounds
            )
            rounds.append(result)

            current_validation=result.get("validation") or current_validation
            conf=float((current_validation.get("scores") or {}).get("validation_confidence",0))
            row={"round":round_no,"confidence":conf,"decision":current_validation.get("decision")}
            history=self.history_store.append(key,row)

            mission=MissionStateSync().apply(mission,round_no,history)

            convergence=result.get("convergence") or {}
            diminishing=DiminishingReturnsDetector().evaluate(history)
            terminal=TerminalDecisionResolver().resolve(
                current_validation,convergence,diminishing,round_no,max_rounds
            )

            self.state.save(key,{
                "round":round_no,"validation":current_validation,"terminal":terminal,"history":history
            })

            if terminal["decision"]!="REVISE":
                break

        convergence=(rounds[-1].get("convergence") if rounds else {}) or {}
        diminishing=DiminishingReturnsDetector().evaluate(history)
        round_no=rounds[-1].get("round",start_round-1) if rounds else start_round-1
        terminal=TerminalDecisionResolver().resolve(
            current_validation,convergence,diminishing,round_no,max_rounds
        )

        confidence=float((current_validation.get("scores") or {}).get("validation_confidence",0))
        build=archive=review=None

        if terminal["action"]=="build":
            build=BuildDispatch().dispatch((rounds[-1] if rounds else {}).get("next_mission"))
        elif terminal["action"]=="archive":
            reason=BoundedExhaustionPolicy().decide(confidence)["reason"] if terminal["decision"]=="EXHAUSTED" else "validation_kill"
            archive=ArchiveDispatch().dispatch(key,reason)
        elif terminal["action"]=="review":
            review=HumanReviewDispatch().dispatch(key,history,terminal["decision"])

        handoff=QueueHandoff().build(terminal,build,archive,review)
        result={
            "success":True,
            "status":"multi_round_revalidation_complete",
            "rounds_executed":len(rounds),
            "rounds":rounds,
            "history":history,
            "final_validation":current_validation,
            "terminal":terminal,
            "handoff":handoff,
        }
        self.audit.append(result)
        return result
