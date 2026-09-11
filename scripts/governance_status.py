#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase689_704 import GovernanceRuntime, SafeMode, EscalationQueue

root=Path.home()/"companyos"
print(json.dumps({
    "runtime":GovernanceRuntime().status(),
    "safe_mode":SafeMode(root).status(),
    "pending_escalations":len(EscalationQueue(root).load()),
},indent=2))
