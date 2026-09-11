#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.actiongov import CEOActionGovernanceController

result=CEOActionGovernanceController(Path.home()/"companyos").run(
    actions=[
        {"kind":"internal_analysis","external":False,"reversible":True,"amount":0},
        {"kind":"internal_research","external":False,"reversible":True,"amount":50},
        {"kind":"send_external_message","external":True,"reversible":False,"amount":0},
        {"kind":"production_deploy","external":True,"reversible":True,"amount":0},
        {"kind":"bank_transfer","external":True,"reversible":False,"amount":1500,"approvals":[]},
        {"kind":"contract_signature","external":True,"reversible":False,"amount":5000,"approvals":["approver_a"]}
    ],
    available_budget=10000,
    recent_action_count=2
)

print(json.dumps(result,indent=2,default=str))
