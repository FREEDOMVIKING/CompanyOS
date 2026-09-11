#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.liveintegration import CEOLiveIntegrationController

result=CEOLiveIntegrationController(Path.home()/"companyos").run(
    connectors=[
        {"name":"research_primary","enabled":True,"capabilities":["research"],"health_score":.95,
         "credentials_ready":True,"fallback_ready":True,"receipts_enabled":True},
        {"name":"research_fallback","enabled":True,"capabilities":["research"],"health_score":.88,
         "credentials_ready":True,"fallback_ready":True,"receipts_enabled":True},
    ],
    actions=[
        {"kind":"internal_research","external":False,"query":"market demand"},
        {"kind":"send_external_message","external":True,"to":"customer@example.com","subject":"Demo"},
        {"kind":"production_deploy","external":True,"artifact":"latest"},
        {"kind":"bank_transfer","external":True,"amount":1500}
    ],
    attempts=[
        {"success":True,"provider":"research_primary"},
        {"success":True,"provider":"research_primary"}
    ],
    env_requirements=[],
    approvals=[]
)

print(json.dumps(result,indent=2,default=str))
