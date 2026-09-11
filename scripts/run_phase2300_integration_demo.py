#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.integrations import CEOIntegrationController

root=Path.home()/"companyos"
ctl=CEOIntegrationController(root)

ctl.registry.register("web_research","provider",["research"],True,{"priority":.9})
ctl.registry.register("build_runner","tool",["build"],True,{"priority":.8})
ctl.registry.register("deploy_bridge","tool",["deploy"],True,{"priority":.85})

result=ctl.run(
    objective="Research, build, validate, deploy, and operate the next venture",
    jobs=[
        {"id":"j1","task_type":"research","capability":"research","priority":9},
        {"id":"j2","task_type":"build","capability":"build","priority":8},
        {"id":"j3","task_type":"deploy","capability":"deploy","action_kind":"production_deploy","priority":7},
        {"id":"j4","task_type":"email","action_kind":"send_external_email","priority":6},
    ],
    providers=[
        {"name":"provider_a","availability":1,"error_rate":.01,"quality":.9,"freshness":.9},
        {"name":"provider_b","availability":.95,"error_rate":.03,"quality":.8,"freshness":.8},
    ],
    scheduled_items=[
        {"name":"daily_metrics","cadence":"daily","task_type":"operations"},
        {"name":"weekly_portfolio_review","cadence":"weekly","task_type":"finance"},
    ]
)

print(json.dumps(result,indent=2,default=str))
