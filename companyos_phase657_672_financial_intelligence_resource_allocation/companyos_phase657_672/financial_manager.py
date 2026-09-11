from .financial_snapshot import FinancialSnapshot
from .burn_runway import BurnRunway
from .profitability import Profitability
from .margin_health import MarginHealth
from .budget_envelope import BudgetEnvelope
from .financial_anomaly import FinancialAnomaly
from .forecast_engine import ForecastEngine
from .allocation_policy import AllocationPolicy

class FinancialManager:
    """669: unified venture financial review."""

    def review(self, metrics, previous=None):
        snap=FinancialSnapshot().build(metrics)
        runway=BurnRunway().calculate(snap)
        profit=Profitability().calculate(snap)
        margin=MarginHealth().evaluate(snap)
        anomaly=FinancialAnomaly().detect(snap,previous or {})
        envelope=BudgetEnvelope().recommend(snap)
        forecasts=ForecastEngine().scenarios(snap)
        allocation=AllocationPolicy().decide({
            "roi_score":float(metrics.get("roi_score",0)),
            "resource_efficiency":float(metrics.get("resource_efficiency",0)),
            "has_anomaly":anomaly["has_anomaly"],
            "runway_months":runway["runway_months"],
        })
        return {
            "success":True,
            "status":"financial_review_ready",
            "snapshot":snap,
            "burn_runway":runway,
            "profitability":profit,
            "margin_health":margin,
            "anomalies":anomaly,
            "budget_envelope":envelope,
            "forecast":forecasts,
            "allocation_recommendation":allocation,
        }
