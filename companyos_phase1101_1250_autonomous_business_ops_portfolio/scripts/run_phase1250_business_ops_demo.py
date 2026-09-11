#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase1101_1250 import CEOBusinessOpsController

result=CEOBusinessOpsController(Path.home()/"companyos").run(
    venture_id="demo_venture",
    channels=[
        {"name":"content","cost":300,"leads":120,"conversion_rate":.08,"recommended_spend":300},
        {"name":"outbound","cost":250,"leads":80,"conversion_rate":.12,"recommended_spend":250},
        {"name":"paid_search","cost":500,"leads":100,"conversion_rate":.05,"recommended_spend":500},
    ],
    acquisition_budget=500,
    leads=[
        {"id":"L1","stage":"lead","pain_confirmed":True,"budget_confirmed":True,"authority_confirmed":True,"timeline_confirmed":False},
        {"id":"L2","stage":"qualified","pain_confirmed":True,"budget_confirmed":True,"authority_confirmed":True,"timeline_confirmed":True},
    ],
    offers=[
        {"name":"basic","traffic":500,"conversions":30,"revenue":3000},
        {"name":"pro","traffic":400,"conversions":35,"revenue":7000},
    ],
    campaigns=[
        {"name":"content","score":.7,"enabled":True},
        {"name":"outbound","score":.8,"enabled":True},
        {"name":"paid_search","score":.4,"enabled":True},
    ],
    customers=[
        {"id":"C1","usage_score":.9,"support_burden":.1,"payment_health":1,"satisfaction":.9},
        {"id":"C2","usage_score":.3,"support_burden":.5,"payment_health":1,"satisfaction":.4},
    ],
    finance={
        "cash":20000,"revenue":8000,"cogs":2000,"opex":3500,
        "committed_spend":2000,"target_cac":100
    },
    kpis={
        "revenue_growth":.35,"retention_rate":.6,"gross_margin":.75,
        "conversion_rate":.08,"reliability":.995
    },
    growth_experiments=[
        {"name":"new_onboarding","expected_impact":.3,"confidence":.8,"effort":1},
        {"name":"pricing_page","expected_impact":.25,"confidence":.9,"effort":.8},
        {"name":"referral_loop","expected_impact":.4,"confidence":.5,"effort":2},
    ],
    growth_results=[
        {"name":"pricing_page","observed_lift":.12,"success_threshold":.08}
    ],
    portfolio_ventures=[
        {"venture_id":"demo_venture","kpi_score":.72,"health":"healthy","net_revenue":6000},
        {"venture_id":"venture_b","kpi_score":.25,"health":"healthy","net_revenue":0},
    ],
)

print(json.dumps(result,indent=2,default=str))
