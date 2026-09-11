from .funnel_analyzer import FunnelAnalyzer
from .retention_analyzer import RetentionAnalyzer
from .revenue_analyzer import RevenueAnalyzer
from .unit_economics import UnitEconomics
from .scale_decision import ScaleDecision

class BusinessOpsManager:
    """462: combine business metrics into a CEO operating review."""

    def review(self, metrics):
        funnel = FunnelAnalyzer().analyze(metrics)
        retention = RetentionAnalyzer().analyze(metrics)
        revenue = RevenueAnalyzer().analyze(metrics)
        economics = UnitEconomics().calculate(metrics)

        evidence = {
            **funnel,
            **retention,
            **revenue,
            **economics,
            "sample_size":int(metrics.get("sample_size",0)),
        }

        return {
            "success":True,
            "status":"business_operations_review_ready",
            "funnel":funnel,
            "retention":retention,
            "revenue":revenue,
            "unit_economics":economics,
            "portfolio_decision":ScaleDecision().decide(evidence),
        }
