#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.enterpriseopt import CEOEnterpriseOptimizer

result=CEOEnterpriseOptimizer(Path.home()/"companyos").run(
    ventures=[
        {"venture_id":"venture_a","growth":.8,"margin":.75,"retention":.82,"reliability":.95,"strategic_fit":.9,"cashflow":5000,"trend":.3,"revenue":20000,"costs":12000,"sector":"construction_ai","capital":7000},
        {"venture_id":"venture_b","growth":.45,"margin":.55,"retention":.6,"reliability":.9,"strategic_fit":.65,"cashflow":500,"trend":.05,"revenue":8000,"costs":7000,"sector":"sales_ai","capital":2500},
        {"venture_id":"venture_c","growth":.1,"margin":.2,"retention":.25,"reliability":.6,"strategic_fit":.3,"cashflow":-1500,"trend":-.2,"revenue":3000,"costs":6000,"sector":"construction_ai","capital":500},
    ],
    capital=10000,
    initiatives=[
        {"name":"expand_best_vertical","impact":.9,"confidence":.8,"alignment":.95,"effort":1,"risk":.15},
        {"name":"new_market_test","impact":.8,"confidence":.55,"alignment":.7,"effort":1.5,"risk":.3},
    ],
    departments=[
        {"name":"research","demand":1.4,"capacity":1},
        {"name":"product","demand":.8,"capacity":1},
        {"name":"growth","demand":1.8,"capacity":1},
    ],
    agents=[
        {"agent_id":"a1","skills":{"research":.95,"growth":.4},"load":.2},
        {"agent_id":"a2","skills":{"product":.9,"growth":.5},"load":.1},
        {"agent_id":"a3","skills":{"growth":.95,"research":.5},"load":.3},
    ],
    work=[
        {"work_id":"w1","skill":"research","priority":.9},
        {"work_id":"w2","skill":"product","priority":.8},
        {"work_id":"w3","skill":"growth","priority":.85},
    ],
    lessons=[
        {"theme":"retention","weight":3},
        {"theme":"pricing","weight":2},
        {"theme":"provider_resilience","weight":4},
    ],
    actions=[
        {"kind":"internal_resource_shift"},
        {"kind":"major_capital_reallocation"},
        {"kind":"venture_retirement"},
    ]
)

print(json.dumps(result,indent=2,default=str))
