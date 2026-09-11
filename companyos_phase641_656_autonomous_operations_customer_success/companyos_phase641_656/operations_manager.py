from .customer_health import CustomerHealth
from .churn_risk import ChurnRisk
from .retention_action import RetentionAction
from .support_triage import SupportTriage
from .service_quality import ServiceQuality
from .customer_success_kpis import CustomerSuccessKPIs
from .bottleneck_detector import BottleneckDetector

class OperationsManager:
    """654: unified operating review."""

    def review_customer(self, customer):
        health=CustomerHealth().score(customer)
        risk=ChurnRisk().evaluate(customer,health)
        return {
            "health":health,
            "churn_risk":risk,
            "retention":RetentionAction().recommend(risk),
        }

    def review_business(self, state):
        return {
            "support_priority":SupportTriage().prioritize(state.get("tickets",[])),
            "service_quality":ServiceQuality().evaluate(state.get("service_metrics",{})),
            "customer_success_kpis":CustomerSuccessKPIs().calculate(state.get("customer_success_metrics",{})),
            "bottleneck":BottleneckDetector().detect(state),
        }
