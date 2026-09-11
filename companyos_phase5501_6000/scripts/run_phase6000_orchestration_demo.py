#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.orchestration import CEOOrchestrationBrain

result=CEOOrchestrationBrain(Path.home()/"companyos").run(
    strategic_goals=[
        {"goal_id":"g_growth","objective":"grow profitable ventures safely","priority":.95},
        {"goal_id":"g_reliability","objective":"maintain continuous healthy operations","priority":.9},
    ],
    systems=[
        {"name":"research_system","capabilities":["research"],"health":.95,"capacity":.8,"healthy":True,"consecutive_failures":0,"backlog":4},
        {"name":"product_system","capabilities":["build"],"health":.9,"capacity":.7,"healthy":True,"consecutive_failures":0,"backlog":2},
        {"name":"ops_system","capabilities":["deploy","operations"],"health":.88,"capacity":.75,"healthy":True,"consecutive_failures":0,"backlog":3},
    ],
    work_items=[
        {"id":"w1","name":"market_research","capability":"research","impact":.8,"urgency":.7,"confidence":.8,"effort":.6,"risk":.1},
        {"id":"w2","name":"build_mvp","capability":"build","impact":.95,"urgency":.8,"confidence":.75,"effort":1,"risk":.2,"depends_on":["w1"]},
        {"id":"w3","name":"deploy_staging","capability":"deploy","impact":.8,"urgency":.6,"confidence":.85,"effort":.7,"risk":.15,"depends_on":["w2"]},
        {"id":"w4","name":"growth_experiment","capability":"growth","impact":.75,"urgency":.5,"confidence":.7,"effort":.8,"risk":.2,"depends_on":["w3"]},
    ],
    memories=[
        {"kind":"customer","importance":.95,"summary":"customers value faster setup"},
        {"kind":"revenue","importance":.85,"summary":"pro plan has stronger economics"},
        {"kind":"failure","importance":.9,"summary":"provider outages require fallback"},
    ],
    signals=[
        {"name":"demand","value":1,"confidence":.85},
        {"name":"unit_economics","value":1,"confidence":.8},
        {"name":"retention","value":.5,"confidence":.7},
    ],
    checkpoint={"state":"previous_cycle_complete"},
    inflight=[],
    actions=[
        {"kind":"internal_analysis"},
        {"kind":"production_deploy"},
        {"kind":"large_marketing_spend","amount":2500},
        {"kind":"contract_signature"},
    ]
)

print(json.dumps(result,indent=2,default=str))
