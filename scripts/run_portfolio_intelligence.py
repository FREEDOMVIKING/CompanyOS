#!/usr/bin/env python3
import json
from companyos_phase561_576 import CEOExecutionBridge

ventures=[
    {"venture_id":"v1","name":"A","evidence":{"validation_score":8,"activation_rate":0.3,"retention_rate":0.35,"revenue_signal":4}},
    {"venture_id":"v2","name":"B","evidence":{"validation_score":6,"activation_rate":0.15,"retention_rate":0.2,"revenue_signal":2}},
]
print(json.dumps(CEOExecutionBridge().portfolio_review(ventures),indent=2))
