#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase905_920 import CEOAdaptiveRecoveryBridge

mission={"mission_id":"demo_validation","mission_type":"validation","context":{
"venture_id":"demo","query":"contractor estimating software demand",
"research_packet":{"evidence":[
{"id":"a","source_class":"public_web","tags":["problem"]},
{"id":"b","source_class":"public_web","tags":["demand"]}
]}}}
validation={"decision":"REVISE","scores":{"problem_evidence":.433,"pricing_validation":.45,"validation_confidence":.657},
"contradictions":{"topics":[],"resolved":True},"revalidation":{"next_attempt":2}}
history=[{"confidence":.657,"decision":"REVISE"},{"confidence":.657,"decision":"REVISE"}]
print(json.dumps(CEOAdaptiveRecoveryBridge(Path.home()/"companyos").build_strategy(
mission,validation,history=history,strategy_history=[],round_no=2),indent=2,default=str))
