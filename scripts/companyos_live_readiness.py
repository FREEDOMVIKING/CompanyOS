#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.livegate import LiveReadinessGate, ActivationState

root = Path.home()/"companyos"
readiness = LiveReadinessGate(root).evaluate()
state = ActivationState(root).write(readiness)

print(json.dumps({
    "success":True,
    "status":"controlled_live_readiness_check_complete",
    "readiness":readiness,
    "activation_state":state
}, indent=2))
