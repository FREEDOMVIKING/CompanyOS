from .market_signal_engine import MarketSignalEngine
from .customer_discovery import CustomerDiscoveryEngine
from .channel_optimizer import ChannelOptimizer
from .pricing_engine import PricingEngine
from .sales_orchestrator import SalesOrchestrator
from .growth_loop import AutonomousGrowthLoop
from .retention_engine import RetentionEngine
from .revenue_optimizer import RevenueOptimizer
from .experiment_portfolio import ExperimentPortfolio
from .market_feedback import MarketFeedbackLoop
from .guardrails import MarketOpsGuardrails
from .state_store import MarketOpsState
from .audit import MarketOpsAudit

class CEOMarketOpsController:
    def __init__(self,root):
        self.state=MarketOpsState(root)
        self.audit=MarketOpsAudit(root)

    def run(self, signals=None, prospects=None, channels=None, offers=None, leads=None,
            cohorts=None, revenue_metrics=None, experiments=None, experiment_results=None,
            actions=None):
        ranked_signals=MarketSignalEngine().score(signals or [])
        segments=CustomerDiscoveryEngine().segment(prospects or [])
        ranked_channels=ChannelOptimizer().rank(channels or [])
        pricing=PricingEngine().recommend(offers or [])
        sales=SalesOrchestrator().next_actions(leads or [])
        growth_selected=AutonomousGrowthLoop().choose(ranked_channels)
        growth_results=AutonomousGrowthLoop().evaluate(experiment_results or [])
        retention=RetentionEngine().evaluate(cohorts or [])
        revenue_actions=RevenueOptimizer().optimize(revenue_metrics or {})
        experiment_rank=ExperimentPortfolio().prioritize(experiments or [])
        feedback=MarketFeedbackLoop().synthesize(ranked_signals,segments,sales,growth_results)
        routing=MarketOpsGuardrails().route(actions or [])
        result={
            "success":True,
            "status":"autonomous_market_execution_growth_cycle_complete",
            "market_signals":ranked_signals,
            "customer_segments":segments,
            "channel_ranking":ranked_channels,
            "pricing":pricing,
            "sales":sales,
            "growth_selected":growth_selected,
            "growth_results":growth_results,
            "retention":retention,
            "revenue_actions":revenue_actions,
            "experiment_portfolio":experiment_rank,
            "market_feedback":feedback,
            **routing
        }
        self.state.save(result)
        self.audit.append("market_ops_cycle",result)
        return result
