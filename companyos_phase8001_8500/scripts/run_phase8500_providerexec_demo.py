#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.providerexec import CEOProviderExecutionController

result=CEOProviderExecutionController(Path.home()/"companyos").run(
    requests=[
        {
            "capability":"research",
            "action":"internal_research",
            "request":{"query":"market demand","seed_items":[{"source":"demo","signal":"positive"}]}
        },
        {
            "capability":"http_api",
            "action":"internal_http_read",
            "request":{"url":"https://example.com","method":"GET"}
        },
        {
            "capability":"command",
            "action":"internal_command",
            "request":{"command":["python","--version"]}
        },
        {
            "capability":"communication",
            "action":"send_external_message",
            "request":{"to":"someone@example.com","subject":"Demo","body":"Test"}
        },
        {
            "capability":"deploy",
            "action":"production_deploy",
            "request":{"environment":"production","artifact":"latest"}
        },
        {
            "capability":"finance_read",
            "action":"read_financial_status",
            "request":{"account_ref":"main","seed_balances":{"cash":10000}}
        }
    ],
    live=False
)
print(json.dumps(result,indent=2,default=str))
