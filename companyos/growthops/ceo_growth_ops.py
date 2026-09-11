from .market_radar import MarketRadar
from .competitor_intelligence import CompetitorIntelligence
from .customer_signal_engine import CustomerSignalEngine
from .opportunity_ranker import OpportunityRanker
from .experiment_engine import ExperimentEngine
from .pricing_optimizer import PricingOptimizer
from .retention_engine import RetentionEngine
from .channel_allocator import ChannelAllocator
from .growth_forecaster import GrowthForecaster
from .learning_memory import LearningMemory
from .approval_router import GrowthApprovalRouter
from .state_store import GrowthState
from .audit import GrowthAudit

class CEOGrowthOpsController:
    def __init__(self,root):
        self.state=GrowthState(root); self.audit=GrowthAudit(root)

    def run(self, market_signals=None, competitors=None, customer_signals=None, opportunities=None,
            experiments=None, offers=None, cohorts=None, channels=None, budget=0,
            current_revenue=0, monthly_growth=0, actions=None):
        exp=ExperimentEngine().decide(experiments or [])
        result={
            "success":True,
            "status":"autonomous_market_intelligence_growth_cycle_complete",
            "market_radar":MarketRadar().scan(market_signals or []),
            "competitor_intelligence":CompetitorIntelligence().analyze(competitors or []),
            "customer_signals":CustomerSignalEngine().aggregate(customer_signals or []),
            "ranked_opportunities":OpportunityRanker().rank(opportunities or []),
            "experiment_decisions":exp,
            "pricing_options":PricingOptimizer().evaluate(offers or []),
            "retention_actions":RetentionEngine().evaluate(cohorts or []),
            "channel_allocations":ChannelAllocator().allocate(channels or [],budget),
            "growth_forecast":GrowthForecaster().forecast(current_revenue,monthly_growth),
            "organizational_learning":LearningMemory().summarize(exp),
            **GrowthApprovalRouter().route(actions or [])
        }
        self.state.save(result); self.audit.append("growth_ops_cycle",result)
        return result
