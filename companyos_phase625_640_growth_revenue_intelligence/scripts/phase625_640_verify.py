#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos_phase625_640 import *

venture={"name":"X","brief":{"product_name":"X","target_customer":"SMB","problem":"slow workflow","value_proposition":"save time"}}
pos=MarketPositioning().build(venture)
assert pos["target_customer"]=="SMB"
assert OfferHypothesis().build(pos)["success_signal"]=="qualified_customer_conversion"
assert PricingExperiment().plan(100)["variants"][1]["price"]==125.0

channels=ChannelStrategy().rank([
    {"name":"a","audience_fit":8,"commercial_intent":8,"estimated_cost":1},
    {"name":"b","audience_fit":3,"commercial_intent":3,"estimated_cost":1},
])
assert channels[0]["name"]=="a"
assert CampaignPlan().build(pos,channels)["automatic_paid_spend"] is False

metrics={
    "qualified_visitors":100,"qualified_leads":20,"activated_users":10,
    "paying_customers":5,"retained_customers":4,"revenue":500,
    "acquisition_spend":100,"average_revenue_per_account":100,
    "gross_margin_rate":0.8,"monthly_churn_rate":0.1,
}
funnel=FunnelMetrics().calculate(metrics)
assert funnel["visitor_to_lead"]==0.2
vanity=VanityGuard().evaluate(metrics)
assert vanity["success_allowed"] is True
assert AcquisitionScore().score(funnel,vanity)>0
econ=UnitEconomics().calculate(metrics)
assert econ["economics_positive"] is True
assert GrowthExperiment().build("x","activation")["automatic_external_spend"] is False
assert RevenueSignal().score(metrics)>=6
assert GrowthDecision().decide(6,8,econ,vanity)["decision"]=="prepare_scale_review"

root=Path(tempfile.mkdtemp(prefix="phase640_"))
assert GrowthAudit(root).append("v1",{"x":1})["venture_id"]=="v1"
mgr=GrowthIntelligenceManager()
assert mgr.plan(venture,channels)["success"] is True
assert mgr.evaluate(metrics)["success"] is True
assert CEOGrowthBridge(root).evaluate("v1",metrics)["success"] is True
assert GrowthRuntime().status()["success"] is True

print(json.dumps({
    "success":True,
    "status":"phase625_640_verification_passed",
    "cycle_status":"phase640_growth_customer_acquisition_revenue_intelligence_ready",
    "market_positioning":True,
    "offer_hypotheses":True,
    "pricing_experiments":True,
    "channel_strategy":True,
    "campaign_planning":True,
    "funnel_metrics":True,
    "vanity_metric_guard":True,
    "acquisition_quality_score":True,
    "unit_economics":True,
    "growth_experiments":True,
    "revenue_signals":True,
    "growth_decisions":True,
    "growth_audit":True,
    "autonomy_mode":"high"
},indent=2))
