from companyos_phase857_872 import CEORevalidationRuntimeBridge
from .stagnation_root_cause import StagnationRootCause
from .strategy_replanner import StrategyReplanner
from .query_strategy_mutator import QueryStrategyMutator
from .provider_mix_optimizer import ProviderMixOptimizer
from .source_gap_targeter import SourceGapTargeter
from .research_budget_allocator import ResearchBudgetAllocator
from .adaptive_retry_policy import AdaptiveRetryPolicy
from .revalidation_strategy_bridge import RevalidationStrategyBridge
from .anti_loop_guard import AntiLoopGuard
from .strategy_state import StrategyState
from .strategy_audit import StrategyAudit

class AdaptiveRecoveryController:
    """918: recover stalled revalidation by changing research strategy, not repeating it."""
    def __init__(self,root):
        self.root=root
        self.state=StrategyState(root)
        self.audit=StrategyAudit(root)

    def build_strategy(self, validation_mission, validation_result, history=None, strategy_history=None, round_no=1):
        ctx=dict((validation_mission or {}).get("context") or {})
        packet=dict(ctx.get("research_packet") or {})
        evidence=list(packet.get("evidence") or [])
        causes=StagnationRootCause().analyze(history,validation_result,evidence)
        replanned=StrategyReplanner().build(causes)
        base_query=ctx.get("query") or ctx.get("objective") or "validate opportunity"
        new_query=QueryStrategyMutator().mutate(base_query,causes,round_no)
        previous_providers=(strategy_history or [{}])[-1].get("providers",[]) if strategy_history else []
        providers=ProviderMixOptimizer().optimize(previous_providers,causes)
        missing=SourceGapTargeter().missing(evidence)
        budget=ResearchBudgetAllocator().allocate(causes,max_attempts=4)

        prior_query=(strategy_history or [{}])[-1].get("query",base_query) if strategy_history else base_query
        retry=AdaptiveRetryPolicy().decide(prior_query,new_query,previous_providers,providers,round_no-1,3)

        plan=CEORevalidationRuntimeBridge(self.root).run(validation_mission,validation_result,history=history)
        plan=RevalidationStrategyBridge().apply(plan,new_query,providers,missing)

        strategy={"query":new_query,"providers":providers,"causes":causes,"replanned":replanned,
                  "missing_sources":missing,"budget":budget,"retry":retry,"plan":plan}
        key=ctx.get("venture_id") or validation_mission.get("mission_id")
        self.state.save(key,strategy)
        self.audit.append({"key":key,"strategy":strategy})
        return strategy
