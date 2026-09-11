#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.productionruntime import CEOProductionRuntime

result=CEOProductionRuntime(Path.home()/"companyos").run_cycle(
    current_stage="operate",
    missions=[
        {"mission_id":"m1","mission_type":"research","priority":9,"created_at":"2026-01-01"},
        {"mission_id":"m2","mission_type":"build","priority":8,"created_at":"2026-01-02"},
        {"mission_id":"m3","mission_type":"growth","priority":7,"created_at":"2026-01-03"},
        {"mission_id":"m4","mission_type":"finance","priority":6,"created_at":"2026-01-04"},
    ],
    services=[
        {"service":"ceo","healthy":True,"restartable":True},
        {"service":"orchestration","healthy":True,"restartable":True},
        {"service":"execution","healthy":True,"restartable":True},
        {"service":"connectors","healthy":True,"restartable":True},
        {"service":"hardening","healthy":True,"restartable":True},
    ],
    approval_queue=[
        {"approval_id":"a1","status":"pending","action":{"kind":"production_deploy"}},
        {"approval_id":"a2","status":"approved","action":{"kind":"send_external_message"}}
    ],
    failures=[],
    preflight_checks={
        "state_store":True,
        "checkpoint":True,
        "queue":True,
        "memory":True,
        "approval_queue":True,
        "health":True,
        "config":True
    }
)

print(json.dumps(result,indent=2,default=str))
