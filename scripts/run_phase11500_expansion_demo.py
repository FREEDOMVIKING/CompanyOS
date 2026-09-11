#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.expansionops import CEOExpansionOpsController

result=CEOExpansionOpsController(Path.home()/"companyos").run(
    opportunities=[
        {
            "name":"regional_construction_ai",
            "market":"south_central_us",
            "demand":.9,"strategic_fit":.95,"margin_potential":.8,"speed_to_market":.8,"risk":.25,
            "regulatory_risk":.1,"capital_risk":.25,"execution_risk":.2,"demand_uncertainty":.15
        },
        {
            "name":"international_smb_ai",
            "market":"international",
            "demand":.8,"strategic_fit":.7,"margin_potential":.85,"speed_to_market":.45,"risk":.5,
            "regulatory_risk":.6,"capital_risk":.45,"execution_risk":.5,"demand_uncertainty":.4
        }
    ],
    ventures=[
        {
            "venture_id":"venture_a",
            "offer":"AI estimating platform",
            "operating_model":"subscription",
            "growth_playbook":"outbound+content",
            "capabilities":["estimating","sales","reporting"],
            "customer_segments":["contractors","smb"]
        },
        {
            "venture_id":"venture_b",
            "capabilities":["sales","crm"],
            "customer_segments":["smb","agencies"]
        }
    ],
    services=[
        {"name":"finance","enabled":True},
        {"name":"customer_support","enabled":True},
        {"name":"research","enabled":True}
    ],
    customers=[
        {"customer_id":"c1","needs":["sales","reporting"]},
        {"customer_id":"c2","needs":["crm"]}
    ],
    customer_portfolio={
        "ventures":["venture_a"],
        "interests":["crm","automation","sales"]
    },
    venture_offers=[
        {"venture_id":"venture_b","name":"sales automation","tags":["crm","sales","automation"]}
    ],
    partners=[
        {"name":"partner_a","reach":.8,"trust":.9,"strategic_fit":.85,"economic_value":.7},
        {"name":"partner_b","reach":.6,"trust":.7,"strategic_fit":.75,"economic_value":.8}
    ],
    actions=[
        {"kind":"internal_market_research"},
        {"kind":"sign_partner_agreement"},
        {"kind":"enter_new_country"},
        {"kind":"major_capital_commitment"}
    ]
)

print(json.dumps(result,indent=2,default=str))
