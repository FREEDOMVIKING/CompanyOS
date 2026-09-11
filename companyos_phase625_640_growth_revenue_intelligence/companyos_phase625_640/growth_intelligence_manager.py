from .market_positioning import MarketPositioning
from .offer_hypothesis import OfferHypothesis
from .channel_strategy import ChannelStrategy
from .campaign_plan import CampaignPlan
from .funnel_metrics import FunnelMetrics
from .vanity_guard import VanityGuard
from .acquisition_score import AcquisitionScore
from .unit_economics import UnitEconomics
from .revenue_signal import RevenueSignal
from .growth_decision import GrowthDecision

class GrowthIntelligenceManager:
    """638: unified acquisition/revenue intelligence."""

    def plan(self, venture, channels):
        positioning=MarketPositioning().build(venture)
        ranked=ChannelStrategy().rank(channels)
        return {
            "success":True,
            "status":"growth_plan_ready",
            "positioning":positioning,
            "offer":OfferHypothesis().build(positioning),
            "campaign":CampaignPlan().build(positioning,ranked),
        }

    def evaluate(self, metrics):
        funnel=FunnelMetrics().calculate(metrics)
        vanity=VanityGuard().evaluate(metrics)
        acquisition=AcquisitionScore().score(funnel,vanity)
        economics=UnitEconomics().calculate(metrics)
        revenue=RevenueSignal().score(metrics)
        decision=GrowthDecision().decide(acquisition,revenue,economics,vanity)
        return {
            "success":True,
            "status":"growth_intelligence_evaluated",
            "funnel":funnel,
            "vanity_guard":vanity,
            "acquisition_score":acquisition,
            "unit_economics":economics,
            "revenue_signal":revenue,
            "decision":decision,
        }
