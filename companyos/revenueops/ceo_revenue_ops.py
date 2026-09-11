from .market_signal import MarketSignalEngine
from .offer_optimizer import OfferOptimizer
from .pricing_engine import PricingExperimentEngine
from .pipeline_engine import RevenuePipelineEngine
from .retention_engine import RetentionEngine
from .unit_economics import UnitEconomicsEngine
from .forecast_engine import RevenueForecastEngine
from .growth_allocator import GrowthAllocator
from .experiment_engine import GrowthExperimentEngine
from .customer_value import CustomerValueEngine
from .authority_boundary import RevenueAuthorityBoundary
from .state_store import RevenueState
from .audit import RevenueAudit

class CEORevenueOpsController:
    def __init__(self,root):
        self.state=RevenueState(root); self.audit=RevenueAudit(root)
    def run(self,signals=None,offers=None,base_price=0,leads=None,customers=None,economics=None,
            current_mrr=0,growth_rate=0,channels=None,growth_budget=0,experiments=None,actions=None):
        e=economics or {}
        result={
          "success":True,"status":"autonomous_revenue_growth_cycle_complete",
          "market_signals":MarketSignalEngine().rank(signals or []),
          "offers":OfferOptimizer().optimize(offers or []),
          "pricing_experiments":PricingExperimentEngine().propose(base_price),
          "pipeline":RevenuePipelineEngine().summarize(leads or []),
          "retention":RetentionEngine().analyze(customers or []),
          "unit_economics":UnitEconomicsEngine().calculate(e.get("revenue",0),e.get("variable_cost",0),e.get("acquisition_cost",0),e.get("retention_months",0)),
          "forecast":RevenueForecastEngine().forecast(current_mrr,growth_rate),
          "growth_allocations":GrowthAllocator().allocate(channels or [],growth_budget),
          "experiments":GrowthExperimentEngine().prioritize(experiments or []),
          "customer_value":CustomerValueEngine().segment(customers or []),
          "authority_boundaries":[{**a,**RevenueAuthorityBoundary().evaluate(a)} for a in (actions or [])]
        }
        self.state.save(result); self.audit.append("revenue_growth_cycle",result); return result
