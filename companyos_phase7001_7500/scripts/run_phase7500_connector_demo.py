#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.connectors import CEOConnectorController

root=Path.home()/"companyos"
ctl=CEOConnectorController(root)

ctl.registry.register("research_primary","provider",["research","news"],.95,True,{"mode":"api"})
ctl.registry.register("research_fallback","provider",["research"],.75,True,{"mode":"public_web"})
ctl.registry.register("communications","provider",["communication"],.9,True,{"mode":"smtp_or_api"})
ctl.registry.register("deployment","tool",["deploy"],.9,True,{"mode":"cli_or_api"})
ctl.registry.register("finance_read","provider",["finance_read"],.85,True,{"mode":"api"})

ctl.credentials.register_env("research_primary",["COMPANYOS_RESEARCH_API_KEY"])
ctl.credentials.register_env("communications",["COMPANYOS_SMTP_PASSWORD"])

result=ctl.run(
    health=[
        {"name":"research_primary","availability":.99,"error_rate":.02,"latency_score":.85,"quality":.95},
        {"name":"research_fallback","availability":1,"error_rate":.05,"latency_score":.7,"quality":.75},
        {"name":"communications","availability":.98,"error_rate":.01,"latency_score":.9,"quality":.9},
        {"name":"deployment","availability":1,"error_rate":0,"latency_score":.9,"quality":.95},
        {"name":"finance_read","availability":.99,"error_rate":.01,"latency_score":.8,"quality":.9},
    ],
    requested_capabilities=["research","communication","deploy","finance_read"],
    actions=[
        {"kind":"internal_research"},
        {"kind":"read_financial_status"},
        {"kind":"send_external_message"},
        {"kind":"production_deploy"},
        {"kind":"bank_transfer","amount":1500}
    ]
)

print(json.dumps(result,indent=2,default=str))
