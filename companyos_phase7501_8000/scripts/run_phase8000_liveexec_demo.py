#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.liveexec import CEOLiveExecutionController

ranked_connectors=[
    {"name":"research_primary","capabilities":["research","news"],"enabled":True,"health_score":.96},
    {"name":"finance_read","capabilities":["finance_read"],"enabled":True,"health_score":.93},
    {"name":"deployment","capabilities":["deploy"],"enabled":True,"health_score":.97},
]

requests=[
    {"capability":"research","action":"internal_research","payload":{"query":"market demand"},"idempotency_key":"research_market_demand_v1"},
    {"capability":"finance_read","action":"read_financial_status","payload":{"account_ref":"main"},"idempotency_key":"finance_status_v1"},
    {"capability":"deploy","action":"production_deploy","payload":{"artifact":"latest"}},
    {"capability":"finance_write","action":"bank_transfer","payload":{"amount":1500}},
]

result=CEOLiveExecutionController(Path.home()/"companyos").run(
    requests=requests,
    ranked_connectors=ranked_connectors,
    simulate=True
)
print(json.dumps(result,indent=2,default=str))
