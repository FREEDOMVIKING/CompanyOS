#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.organization import CEOOrganizationController

root=Path.home()/"companyos"

result=CEOOrganizationController(root).run(
    strategic_goal="Operate and grow a portfolio of autonomous AI businesses profitably and safely",
    tasks=[
        {"id":"t1","type":"execution","impact":.9,"urgency":.8,"confidence":.85,"risk":.2,"effort":1},
        {"id":"t2","type":"research","impact":.7,"urgency":.5,"confidence":.8,"risk":.1,"effort":.8},
        {"id":"t3","type":"growth","impact":.8,"urgency":.7,"confidence":.65,"risk":.3,"effort":1.2},
    ],
    departments=[
        {"name":"product","capacity":.8,"skill_match":{"execution":.95,"research":.4,"growth":.4}},
        {"name":"research","capacity":.7,"skill_match":{"execution":.4,"research":.95,"growth":.5}},
        {"name":"growth","capacity":.6,"skill_match":{"execution":.5,"research":.5,"growth":.95}},
    ],
    workload={"research":2,"product":2,"growth":1,"operations":1},
    agent_results=[
        {"agent_id":"a1","quality":.9,"speed":.8,"reliability":.95,"learning":.9},
        {"agent_id":"a2","quality":.5,"speed":.6,"reliability":.5,"learning":.6},
    ],
    budget_requests=[
        {"department":"growth","expected_value":.8,"confidence":.75,"urgency":.7,"requested":600,"autonomous_cap":500},
        {"department":"product","expected_value":.9,"confidence":.9,"urgency":.8,"requested":400,"autonomous_cap":500},
    ],
    total_budget=1000,
    resource_claims=[
        {"resource":"builder","department":"product","priority":.9},
        {"resource":"builder","department":"growth","priority":.5},
    ],
    ventures=[
        {"venture_id":"venture_a","score":.82,"health":"healthy"},
        {"venture_id":"venture_b","score":.48,"health":"healthy"},
        {"venture_id":"venture_c","score":.2,"health":"healthy"},
    ],
    outcomes={"g1":.7,"g2":.8,"g3":.75,"g4":.6,"g5":.5},
    failures=[
        {"kind":"department_overload","department":"research"},
        {"kind":"agent_failure","agent_id":"a2"},
    ],
    actions=[
        {"kind":"internal_research"},
        {"kind":"contract_signature"},
        {"kind":"bank_transfer","amount":1200},
    ],
)

print(json.dumps(result,indent=2,default=str))
