#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.marketops import CEOMarketOpsController

result=CEOMarketOpsController(Path.home()/"companyos").run(
    signals=[
        {"name":"estimating_ai","demand":.9,"pain":.85,"urgency":.75,"budget":.8,"competition_gap":.65,"evidence_quality":.9},
        {"name":"generic_content","demand":.5,"pain":.3,"urgency":.25,"budget":.35,"competition_gap":.1,"evidence_quality":.5},
    ],
    prospects=[
        {"segment":"small_contractors","pain":.9,"budget_signal":.7,"urgency":.85},
        {"segment":"small_contractors","pain":.8,"budget_signal":.8,"urgency":.75},
        {"segment":"enterprise_construction","pain":.7,"budget_signal":.95,"urgency":.6},
    ],
    channels=[
        {"name":"outbound","cac":50,"ltv":700,"conversion_rate":.12,"scalability":.75,"lead_quality":.9},
        {"name":"content","cac":35,"ltv":500,"conversion_rate":.08,"scalability":.9,"lead_quality":.75},
        {"name":"paid_search","cac":120,"ltv":600,"conversion_rate":.06,"scalability":.95,"lead_quality":.65},
    ],
    offers=[
        {"name":"starter","price":49,"conversion_rate":.12,"retention_rate":.65,"gross_margin":.8},
        {"name":"pro","price":129,"conversion_rate":.09,"retention_rate":.82,"gross_margin":.86},
    ],
    leads=[
        {"id":"L1","pain_confirmed":True,"budget_confirmed":True,"authority_confirmed":True,"timeline_confirmed":True,"engagement":.9},
        {"id":"L2","pain_confirmed":True,"budget_confirmed":True,"authority_confirmed":False,"timeline_confirmed":False,"engagement":.5},
    ],
    cohorts=[
        {"name":"month1","retention_rate":.62,"engagement":.7,"satisfaction":.8},
        {"name":"month2","retention_rate":.38,"engagement":.45,"satisfaction":.55},
    ],
    revenue_metrics={"gross_margin":.72,"conversion_rate":.045,"retention_rate":.48,"arpu_growth":.08},
    experiments=[
        {"name":"pricing_v2","impact":.8,"confidence":.8,"effort":1,"risk":.15},
        {"name":"onboarding_v3","impact":.75,"confidence":.7,"effort":1.2,"risk":.1},
        {"name":"referral_loop","impact":.6,"confidence":.5,"effort":1.5,"risk":.2},
    ],
    experiment_results=[
        {"name":"pricing_v2","observed_lift":.14,"success_threshold":.08},
        {"name":"onboarding_v3","observed_lift":.03,"success_threshold":.06},
    ],
    actions=[
        {"kind":"internal_analysis"},
        {"kind":"build_landing_page"},
        {"kind":"send_external_email"},
        {"kind":"large_marketing_spend","amount":1500},
    ]
)

print(json.dumps(result,indent=2,default=str))
