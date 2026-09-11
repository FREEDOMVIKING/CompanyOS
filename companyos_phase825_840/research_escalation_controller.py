from companyos_phase777_792 import EvidenceCollector, ProviderErrorNormalizer
from .failure_classifier import FailureClassifier
from .provider_escalation_policy import ProviderEscalationPolicy
from .query_reformulator import QueryReformulator
from .evidence_gap_analyzer import EvidenceGapAnalyzer
from .provider_retry_budget import ProviderRetryBudget
from .adaptive_backoff import AdaptiveBackoff
from .escalation_state import EscalationState
from .provider_chain_builder import ProviderChainBuilder
from .evidence_accumulator import EvidenceAccumulator
from .confidence_progress import ConfidenceProgress
from .promotion_threshold import PromotionThreshold
from .deferred_recovery_policy import DeferredRecoveryPolicy
from .research_escalation_audit import ResearchEscalationAudit

class ResearchEscalationController:
    """838: escalate failed/weak research across providers until promotion or bounded defer."""

    def __init__(self, root):
        self.root = root
        self.state = EscalationState(root)
        self.audit = ResearchEscalationAudit(root)

    def run(self, mission, provider_results=None, max_total_attempts=8):
        provider_results = provider_results or {}
        ctx = dict((mission or {}).get("context") or {})
        query = ctx.get("query") or ctx.get("objective") or ctx.get("research_goal") or "collect market evidence"
        query_type = ctx.get("query_type") or "market"
        preferred = ctx.get("provider_hint") or "github"
        existing = list(ctx.get("evidence") or [])

        chain = ProviderChainBuilder().build(preferred, query_type)
        accumulated = EvidenceAccumulator().merge([], existing)

        total_attempts = 0
        execution = []
        current_query = query

        for round_no, provider in enumerate(chain, 1):
            provider_attempts = 0
            while provider_attempts < 2 and total_attempts < max_total_attempts:
                provider_attempts += 1
                total_attempts += 1

                context = {"provider_results": provider_results}
                result = EvidenceCollector().collect(provider, current_query, context)
                failure = FailureClassifier().classify(result)

                before = list(accumulated)
                accumulated = EvidenceAccumulator().merge(accumulated, result.get("items", []))
                progress = ConfidenceProgress().evaluate(before, accumulated)
                threshold = PromotionThreshold().evaluate(accumulated)

                execution.append({
                    "round": round_no,
                    "provider": provider,
                    "query": current_query,
                    "success": result.get("success"),
                    "failure_kind": failure.get("kind"),
                    "evidence_added": len(result.get("items",[])),
                    "confidence": threshold.get("confidence"),
                    "progress": progress,
                })

                self.audit.append({
                    "mission_id": mission.get("mission_id"),
                    "provider": provider,
                    "round": round_no,
                    "failure": failure,
                    "threshold": threshold,
                })

                if threshold["passed"]:
                    self.state.update(
                        mission.get("mission_id"),
                        status="promoted",
                        total_attempts=total_attempts,
                        provider=provider,
                        confidence=threshold["confidence"],
                    )
                    return {
                        "success": True,
                        "status": "research_escalation_promoted",
                        "promote": True,
                        "evidence": accumulated,
                        "threshold": threshold,
                        "execution": execution,
                        "final_provider": provider,
                        "final_query": current_query,
                    }

                gaps = EvidenceGapAnalyzer().analyze(accumulated)
                action = ProviderEscalationPolicy().decide(
                    failure, provider_attempts, total_attempts, max_total=max_total_attempts
                )

                if action == "retry_provider":
                    continue

                if action == "reformulate_and_switch":
                    current_query = QueryReformulator().reformulate(
                        current_query, gaps.get("missing"), round_no
                    )
                    break

                if action == "switch_provider":
                    break

                if action == "defer":
                    delay = AdaptiveBackoff().seconds(failure.get("kind"), total_attempts)
                    deferred = DeferredRecoveryPolicy().build(
                        mission, delay, "escalation_budget_exhausted", provider_hint=provider
                    )
                    self.state.update(
                        mission.get("mission_id"),
                        status="deferred",
                        total_attempts=total_attempts,
                        provider=provider,
                    )
                    return {
                        "success": True,
                        "status": "research_escalation_deferred",
                        "promote": False,
                        "evidence": accumulated,
                        "execution": execution,
                        "deferred_mission": deferred,
                    }

            gaps = EvidenceGapAnalyzer().analyze(accumulated)
            current_query = QueryReformulator().reformulate(
                current_query, gaps.get("missing"), round_no
            )

        delay = AdaptiveBackoff().seconds("provider_error", total_attempts)
        deferred = DeferredRecoveryPolicy().build(
            mission, delay, "provider_chain_exhausted", provider_hint=(chain[-1] if chain else preferred)
        )
        self.state.update(
            mission.get("mission_id"),
            status="deferred",
            total_attempts=total_attempts,
            provider=(chain[-1] if chain else preferred),
        )

        return {
            "success": True,
            "status": "research_escalation_deferred",
            "promote": False,
            "evidence": accumulated,
            "execution": execution,
            "deferred_mission": deferred,
        }
