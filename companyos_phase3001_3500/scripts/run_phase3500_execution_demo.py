#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.execution import CEOExecutionFabric

result=CEOExecutionFabric(Path.home()/"companyos").run(
    objective="Continuously discover, build, operate, and optimize profitable ventures",
    workers=[
        {"worker_id":"research_1","capabilities":["research"],"reliability":.95},
        {"worker_id":"builder_1","capabilities":["build"],"reliability":.9},
        {"worker_id":"ops_1","capabilities":["deploy","operations"],"reliability":.92},
        {"worker_id":"growth_1","capabilities":["growth"],"reliability":.88},
    ],
    schedules=[
        {"name":"market_scan","cadence":"daily","capability":"research","priority":9},
        {"name":"build_queue","cadence":"daily","capability":"build","priority":8},
        {"name":"health_check","cadence":"hourly","capability":"operations","priority":10},
        {"name":"growth_optimization","cadence":"daily","capability":"growth","priority":7},
    ],
    services=[
        {"service":"ceo_daemon","healthy":True,"load":.4},
        {"service":"research_worker","healthy":True,"load":.7},
        {"service":"build_worker","healthy":False,"reason":"crash"},
    ],
    failures=[
        {"kind":"worker_crash","worker":"build_worker"},
        {"kind":"provider_failure","provider":"provider_a"},
    ],
    actions=[
        {"kind":"internal_analysis"},
        {"kind":"production_deploy"},
        {"kind":"bank_transfer","amount":1500},
    ],
    spawn_venture=True,
)

print(json.dumps(result,indent=2,default=str))
