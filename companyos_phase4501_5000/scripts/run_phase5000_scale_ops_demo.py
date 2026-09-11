#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.scaleops import CEOScaleOpsController

result=CEOScaleOpsController(Path.home()/"companyos").run(
    finance={
        "revenue":20000,
        "cogs":4000,
        "opex":7000,
        "growth_investment":2000,
        "opening_cash":30000,
        "inflows":22000,
        "outflows":15000,
        "scale_budget":5000,
        "revenue_growth":.35
    },
    opportunities=[
        {"name":"outbound_scale","expected_roi":2.2,"confidence":.8,"capacity":.9},
        {"name":"content_scale","expected_roi":1.8,"confidence":.75,"capacity":1.0},
        {"name":"new_market","expected_roi":3.0,"confidence":.45,"capacity":.6},
    ],
    vendors=[
        {"name":"provider_a","reliability":.95,"cost_score":.7,"security":.9,"lockin_risk":.3},
        {"name":"provider_b","reliability":.9,"cost_score":.9,"security":.8,"lockin_risk":.2},
    ],
    obligations=[
        {"key":"privacy","description":"privacy controls"},
        {"key":"security","description":"security controls"},
        {"key":"tax","description":"tax records"},
    ],
    compliance_evidence=["privacy","security"],
    risks=[
        {"name":"single_provider","likelihood":.5,"impact":.7,"detectability":.8},
        {"name":"cashflow_squeeze","likelihood":.3,"impact":.9,"detectability":.6},
    ],
    decisions=[
        {"name":"increase_ad_spend","reversible":True,"external":True,"financial_exposure":300},
        {"name":"sign_annual_vendor_contract","reversible":False,"external":True,"financial_exposure":5000},
    ],
    scenarios={
        "base":{"survival":True,"growth":.25},
        "upside":{"survival":True,"growth":.5},
        "downside":{"survival":True,"growth":-.1}
    },
    ventures=[
        {"venture_id":"venture_a","score":.82,"cashflow":5000},
        {"venture_id":"venture_b","score":.55,"cashflow":500},
        {"venture_id":"venture_c","score":.22,"cashflow":-1000},
    ],
    actions=[
        {"kind":"internal_financial_model"},
        {"kind":"large_marketing_spend","amount":2000},
        {"kind":"contract_signature"},
        {"kind":"bank_transfer","amount":3000},
    ]
)

print(json.dumps(result,indent=2,default=str))
