#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase873_888 import CEORevalidationExecutionBridge
mission={"mission_id":"demo_validation","mission_type":"validation","attempts":0,
"context":{"venture_id":"demo","research_confidence":.82,"research_packet":{"confidence":.82,"contradictions":{"topics":[]},
"evidence":[{"id":"a","source_class":"official","tags":["problem","risk"]},{"id":"b","source_class":"reputable_news","tags":["demand","alternatives"]},{"id":"c","source_class":"competitor_site","tags":["pricing"]}]}}}
validation={"decision":"REVISE","scores":{"problem_evidence":.4,"pricing_validation":.388,"validation_confidence":.635},
"contradictions":{"topics":[],"resolved":True},"revalidation":{"next_attempt":1}}
providers={"public_web":{"success":True,"items":[{"id":"p1","source_class":"public_web","tags":["problem","demand"]},
{"id":"p2","source_class":"public_web","tags":["pricing"],"willingness_to_pay_score":1.0}]},
"official":{"success":True,"items":[{"id":"o1","source_class":"official","tags":["problem","pricing"],"willingness_to_pay_score":1.0}]}}
print(json.dumps(CEORevalidationExecutionBridge(Path.home()/"companyos").run_round(mission,validation,providers,history=[],round_no=1),indent=2,default=str))
