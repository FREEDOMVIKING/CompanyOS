#!/usr/bin/env python3
import json, os
from pathlib import Path
from companyos.liveintegration import FinalLiveIntegrationStatus, LiveExecutionPolicy

root=Path.home()/"companyos"
policy=LiveExecutionPolicy()
print(json.dumps({
    "success":True,
    "status":"final_live_integration_status",
    "integration":FinalLiveIntegrationStatus().status(),
    "policy":policy.snapshot(),
    "note":"Live execution only runs when COMPANYOS_ENABLE_LIVE_FINANCIAL_EXECUTION=true and all runtime gates pass."
}, indent=2))
