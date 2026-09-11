#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos_phase657_672 import *

metrics={
    "revenue":5000,"mrr":4500,"variable_costs":800,"fixed_costs":1200,
    "cash_available":20000,"acquisition_spend":700,"paying_customers":30,
    "gross_margin_rate":0.8,"monthly_churn_rate":0.05,
    "roi_score":8,"resource_efficiency":1.2
}

snap=FinancialSnapshot().build(metrics)
assert snap["revenue"]==5000
runway=BurnRunway().calculate(snap)
assert runway["self_sustaining"] is True
profit=Profitability().calculate(snap)
assert profit["profitable"] is True
assert MarginHealth().evaluate(snap)["level"]=="strong"
assert BudgetEnvelope().recommend(metrics)["automatic_spend_authorized"] is False
assert ROIScore().score({"incremental_value":200,"resource_cost":100})>5
assert ResourceEfficiency().score({"progress_score":5,"resource_cost":2,"revenue_signal":4})>0

ranked=PortfolioCapitalRank().rank([
    {"venture_id":"a","roi_score":8,"resource_efficiency":2,"revenue_signal":5},
    {"venture_id":"b","roi_score":4,"resource_efficiency":1,"revenue_signal":2},
])
assert ranked[0]["venture_id"]=="a"

assert FinancialAnomaly().detect(
    {"revenue":100,"variable_costs":200,"acquisition_spend":100,"paying_customers":0},
    {"revenue":1000,"variable_costs":50}
)["has_anomaly"] is True

assert ForecastEngine().scenarios(metrics)["base"]["next_month_mrr"]>0
assert AllocationPolicy().decide({
    "roi_score":8,"resource_efficiency":1.2,"has_anomaly":False,"runway_months":12
})["decision"]=="prepare_scale_review"

root=Path(tempfile.mkdtemp(prefix="phase672_"))
assert FinancialAudit(root).append("v1",{"x":1})["venture_id"]=="v1"

review=FinancialManager().review(metrics)
assert review["success"] is True
bridge=CEOFinancialBridge(root)
assert bridge.review_venture("v1",metrics)["success"] is True
assert bridge.rank_portfolio([{
    "venture_id":"v1","incremental_value":200,"resource_cost":100,
    "progress_score":5,"revenue_signal":4
}])[0]["venture_id"]=="v1"
assert FinancialHealth().evaluate(review)["healthy"] is True
assert FinancialRuntime().status()["success"] is True

print(json.dumps({
    "success":True,
    "status":"phase657_672_verification_passed",
    "cycle_status":"phase672_financial_intelligence_resource_allocation_ready",
    "financial_snapshots":True,
    "burn_runway":True,
    "profitability":True,
    "margin_health":True,
    "budget_envelopes":True,
    "roi_scoring":True,
    "resource_efficiency":True,
    "portfolio_capital_ranking":True,
    "financial_anomaly_detection":True,
    "forecast_scenarios":True,
    "allocation_policy":True,
    "financial_audit":True,
    "automatic_financial_transfers":False,
    "automatic_purchases":False,
    "autonomy_mode":"high"
},indent=2))
