from companyos_phase905_920 import CEOAdaptiveRecoveryBridge
from .adaptive_plan_executor import AdaptivePlanExecutor
from .adaptive_result_normalizer import AdaptiveResultNormalizer
from .novel_evidence_filter import NovelEvidenceFilter
from .signal_quality_filter import SignalQualityFilter
from .adaptive_evidence_store import AdaptiveEvidenceStore
from .validation_feedback_bridge import ValidationFeedbackBridge
from .confidence_improvement_gate import ConfidenceImprovementGate
from .adaptive_round_decision import AdaptiveRoundDecision
from .diminishing_return_guard import DiminishingReturnGuard
from .strategy_execution_state import StrategyExecutionState
from .strategy_execution_audit import StrategyExecutionAudit

class AdaptiveClosedLoopController:
    """933: execute changed strategy, feed evidence back, and measure real improvement."""
    def __init__(self,root):
        self.root=root
        self.store=AdaptiveEvidenceStore(root)
        self.state=StrategyExecutionState(root)
        self.audit=StrategyExecutionAudit(root)

    def run(self, mission, validation, provider_results=None, history=None, strategy_history=None,
            strategy_attempt=1, execution_history=None):
        strategy=CEOAdaptiveRecoveryBridge(self.root).build_strategy(
            mission,validation,history=history or [],strategy_history=strategy_history or [],
            round_no=strategy_attempt
        )

        executions=AdaptivePlanExecutor().execute(strategy,provider_results or {})
        raw=AdaptiveResultNormalizer().normalize(executions)

        existing=list((((mission or {}).get("context") or {}).get("research_packet") or {}).get("evidence",[]) or [])
        novelty=NovelEvidenceFilter().apply(existing,raw)
        quality=SignalQualityFilter().apply(novelty.get("accepted",[]))
        accepted=quality.get("kept",[])

        key=((mission or {}).get("context") or {}).get("venture_id") or mission.get("mission_id")
        self.store.save(key,strategy_attempt,accepted)

        before=float((validation.get("scores") or {}).get("validation_confidence",0))
        feedback=ValidationFeedbackBridge(self.root).apply(mission,accepted)
        rerun=feedback["validation"]
        after=float((rerun.get("scores") or {}).get("validation_confidence",0))
        improvement=ConfidenceImprovementGate().evaluate(before,after)

        round_row={"strategy_attempt":strategy_attempt,"confidence_delta":improvement["delta"],
                   "novelty":novelty["novelty"],"decision":rerun.get("decision")}
        execution_history=list(execution_history or [])+[round_row]
        diminishing=DiminishingReturnGuard().evaluate(execution_history)

        decision=AdaptiveRoundDecision().decide(
            rerun,improvement,novelty["novelty"],strategy_attempt
        )
        if diminishing["stop"] and decision["decision"]=="REVISE":
            decision={"decision":"HUMAN_REVIEW","action":"review","reason":"diminishing_returns"}

        result={
            "success":True,
            "status":"adaptive_strategy_execution_complete",
            "strategy":strategy,
            "executions":executions,
            "raw_evidence_count":len(raw),
            "novelty":novelty,
            "quality_filter":{"kept_count":len(accepted),"dropped_count":len(quality.get("dropped",[]))},
            "accepted_evidence":accepted,
            "validation":rerun,
            "improvement":improvement,
            "diminishing_returns":diminishing,
            "decision":decision,
            "updated_mission":feedback["mission"],
            "execution_history":execution_history,
        }
        self.state.save(key,result)
        self.audit.append(result)
        return result
