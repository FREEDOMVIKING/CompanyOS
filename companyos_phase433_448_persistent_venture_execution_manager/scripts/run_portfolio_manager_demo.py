#!/usr/bin/env python3
import json
from companyos_phase433_448 import CEOPortfolioRouter

ventures = [
    {
        "venture_id":"venture_a",
        "name":"Workflow Automation Copilot",
        "status":"building",
        "priority":0.9,
        "failures":0,
        "retries":0,
        "metrics":{"validation_score":9,"revenue_signal":3,"retention_signal":2},
        "specialist_jobs":[
            {"id":"T1","task":"finalize product brief","depends_on":[]},
            {"id":"T2","task":"implement core value loop","depends_on":["T1"]},
        ],
        "completed_task_ids":[],
    },
    {
        "venture_id":"venture_b",
        "name":"AI Estimating & Proposal Copilot",
        "status":"queued",
        "priority":0.8,
        "failures":0,
        "retries":0,
        "metrics":{"validation_score":8,"revenue_signal":2,"retention_signal":1},
        "specialist_jobs":[
            {"id":"T1","task":"finalize product brief","depends_on":[]},
        ],
        "completed_task_ids":[],
    },
    {
        "venture_id":"venture_c",
        "name":"Reporting Intelligence",
        "status":"paused",
        "priority":0.4,
        "failures":2,
        "retries":1,
        "metrics":{"validation_score":5},
        "blocked_reason":"dependency_failure",
        "specialist_jobs":[],
        "completed_task_ids":[],
    },
]

print(json.dumps(CEOPortfolioRouter().route(ventures, max_active=2), indent=2))
