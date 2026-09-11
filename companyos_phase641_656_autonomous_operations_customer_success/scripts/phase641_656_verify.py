#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos_phase641_656 import *

customer={
    "usage_score":0.2,"value_realization":0.3,"satisfaction_score":0.3,
    "open_critical_issues":1,"usage_change_30d":-0.5,"unresolved_tickets":3,
}
health=CustomerHealth().score(customer)
assert health["status"]=="at_risk"
risk=ChurnRisk().evaluate(customer,health)
assert risk["at_risk"] is True
assert RetentionAction().recommend(risk)["actions"]

tickets=[
    {"id":"1","severity":"low"},
    {"id":"2","severity":"critical","blocks_core_value":True},
]
assert SupportTriage().prioritize(tickets)[0]["id"]=="2"
assert FeedbackAggregator().summarize([{"themes":["speed"]},{"themes":["speed","ui"]}])["themes"][0]["count"]==2
assert IncidentManager().classify({"core_service_down":True})["severity"]=="critical"
assert len(RecurringOperations().schedule())>=5
assert ServiceQuality().evaluate({"uptime":0.995,"error_rate":0.01,"core_workflow_success_rate":0.97})["healthy"] is True
assert SLATracker().evaluate([{"within_target":True},{"within_target":False}])["within_target_rate"]==0.5
assert FeedbackRouter().route({"category":"bug"})["destination"]=="product_quality"

kpis=CustomerSuccessKPIs().calculate({
    "customers_start":10,"customers_retained":9,
    "starting_recurring_revenue":1000,"churned_revenue":50,"expansion_revenue":100
})
assert kpis["logo_retention_rate"]==0.9
assert BottleneckDetector().detect({"critical_incidents":1})["bottleneck"]=="reliability"

root=Path(tempfile.mkdtemp(prefix="phase656_"))
assert OperationsAudit(root).append("x",{})["event"]=="x"
mgr=OperationsManager()
assert mgr.review_customer(customer)["churn_risk"]["at_risk"] is True
assert CEOOperationsBridge(root).review_customer(customer)["health"]
assert OperationsRuntime().status()["success"] is True

print(json.dumps({
    "success":True,
    "status":"phase641_656_verification_passed",
    "cycle_status":"phase656_autonomous_operations_customer_success_ready",
    "customer_health":True,
    "support_triage":True,
    "feedback_aggregation":True,
    "churn_risk":True,
    "retention_actions":True,
    "incident_management":True,
    "recurring_operations":True,
    "service_quality":True,
    "sla_tracking":True,
    "feedback_routing":True,
    "customer_success_kpis":True,
    "bottleneck_detection":True,
    "operations_audit":True,
    "autonomy_mode":"high"
},indent=2))
