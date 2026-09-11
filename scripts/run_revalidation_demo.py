#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase857_872 import CEORevalidationRuntimeBridge
validation={"decision":"REVISE","scores":{"research_confidence":.82,"problem_evidence":.4,"pricing_validation":.388,"validation_confidence":.635},
"contradictions":{"topics":[],"resolved":True},"revalidation":{"next_attempt":1}}
mission={"mission_id":"phase841_demo_validation","attempts":0,"context":{"venture_id":"demo_venture"}}
print(json.dumps(CEORevalidationRuntimeBridge(Path.home()/"companyos").run(mission,validation),indent=2))
