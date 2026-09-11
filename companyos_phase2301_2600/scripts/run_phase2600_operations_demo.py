#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.operations import CEOOperationsController

result=CEOOperationsController(Path.home()/"companyos").run(
    goals=[
        {"goal_id":"growth","objective":"increase profitable customer growth","target":1,"progress":.55,"horizon":"monthly"},
        {"goal_id":"reliability","objective":"maintain healthy autonomous runtime","target":1,"progress":.9,"horizon":"daily"},
    ],
    events=[
        {"kind":"customer_signal","payload":{"importance":.9}},
        {"kind":"revenue_signal","payload":{"importance":.8}},
        {"kind":"incident","payload":{"importance":.95}},
    ],
    cadence={
        "daily":["review metrics","process priority queue","check incidents"],
        "weekly":["review departments","reallocate resources"],
        "monthly":["review strategy","portfolio optimization"]
    },
    department_updates=[
        {"department":"sales","blockers":[],"handoffs":[{"to":"finance","task":"pricing approval"}]},
        {"department":"product","blockers":["needs customer evidence"],"handoffs":[{"to":"research","task":"collect evidence"}]},
        {"department":"operations","blockers":[],"handoffs":[]},
    ],
    metrics={
        "revenue_growth":.35,
        "retention_rate":.46,
        "gross_margin":.72,
        "conversion_rate":.04,
        "reliability":.99,
        "customer_satisfaction":.82,
        "incident_rate":.02
    },
    failures=[
        {"kind":"provider_failure","provider":"provider_a"},
        {"kind":"queue_stall","queue":"research"}
    ],
    experiments=[
        {"name":"pricing_page","success":True},
        {"name":"onboarding_v2","success":False}
    ],
    decisions=[
        {"name":"channel_mix","outcome":"shift_budget_to_outbound"}
    ],
    initiatives=[
        {"name":"retention_program","expected_value":.8,"confidence":.8,"effort":1},
        {"name":"conversion_rework","expected_value":.7,"confidence":.7,"effort":1.2},
        {"name":"new_market","expected_value":.9,"confidence":.4,"effort":2}
    ],
    actions=[
        {"kind":"internal_analysis"},
        {"kind":"contract_signature"},
        {"kind":"bank_transfer","amount":1200}
    ]
)

print(json.dumps(result,indent=2,default=str))
