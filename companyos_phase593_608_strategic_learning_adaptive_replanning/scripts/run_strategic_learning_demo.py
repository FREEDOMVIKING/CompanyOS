#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase593_608 import CEOLearningBridge

root = Path.home() / "companyos"
bridge = CEOLearningBridge(root)

result = bridge.apply(
    "venture_demo",
    "operations",
    "operations",
    {
        "mission_success":True,
        "activation_rate":0.06,
        "retention_rate":0.04,
        "revenue_signal":0.0,
    },
    {
        "mission_id":"mission_demo",
        "mission_type":"operations",
        "priority":0.8,
        "context":{},
    },
    confidence=0.6,
)

print(json.dumps(result, indent=2, default=str))
