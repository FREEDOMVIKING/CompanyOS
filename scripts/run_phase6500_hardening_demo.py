#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.hardening import ProductionHardeningController

root=Path.home()/"companyos"
result=ProductionHardeningController(root).run(
    components=[
        {"name":"ceo_runtime","heartbeat":True,"error_rate":.01,"saturation":.45,"backlog":4},
        {"name":"research_workers","heartbeat":True,"error_rate":.02,"saturation":.6,"backlog":7},
        {"name":"build_workers","heartbeat":True,"error_rate":.01,"saturation":.5,"backlog":3},
    ],
    metrics={"availability":.999,"success_rate":.995,"error_rate":.01},
    slo_targets={"availability":.99,"success_rate":.98,"error_rate":.05},
    incident_signals=[
        {"name":"provider_latency","impact":.35},
        {"name":"build_worker_crash","impact":.75}
    ],
    config={"max_parallel":8,"retry_limit":4,"runtime_mode":"continuous"},
    required_config=["max_parallel","retry_limit","runtime_mode"],
    secret_config={"api_key":"${COMPANYOS_PROVIDER_API_KEY}","smtp_password":"env:COMPANYOS_SMTP_PASSWORD"},
    release={"current_artifact":"phase6500","previous_artifact":"phase6000"},
    integrity_paths=[root/"scripts/companyos_orchestration.sh", root/"scripts/companyos_control.sh"],
    chaos_scenarios=[
        {"kind":"worker_failure"},
        {"kind":"provider_failure"},
        {"kind":"queue_stall"}
    ],
    workload=12,
    workers=6
)
print(json.dumps(result,indent=2,default=str))
