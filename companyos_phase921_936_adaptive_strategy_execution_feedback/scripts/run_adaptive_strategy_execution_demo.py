#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase921_936 import CEOAdaptiveExecutionBridge

mission={"mission_id":"demo_validation","mission_type":"validation","attempts":0,"context":{
"venture_id":"demo","query":"contractor estimating software demand",
"research_confidence":.82,
"research_packet":{"confidence":.82,"contradictions":{"topics":[]},
"evidence":[
{"id":"a","source_class":"public_web","tags":["problem"]},
{"id":"b","source_class":"public_web","tags":["demand"]}
]}}}

validation={"decision":"REVISE","scores":{"research_confidence":.82,"problem_evidence":.433,
"pricing_validation":.45,"validation_confidence":.657},
"contradictions":{"topics":[],"resolved":True},"revalidation":{"next_attempt":2}}

history=[{"confidence":.657,"decision":"REVISE"},{"confidence":.657,"decision":"REVISE"}]

providers={
"official":{"success":True,"items":[
{"id":"o1","source_class":"official","tags":["problem","pricing"],"willingness_to_pay_score":1.0},
{"id":"o2","source_class":"official","tags":["pricing","alternatives"],"willingness_to_pay_score":1.0}
]},
"reputable_news":{"success":True,"items":[
{"id":"n1","source_class":"reputable_news","tags":["demand","alternatives"]},
{"id":"n2","source_class":"reputable_news","tags":["problem","demand"]}
]},
"public_web":{"success":True,"items":[
{"id":"p1","source_class":"public_web","tags":["problem","pricing"],"willingness_to_pay_score":.9}
]}
}

result=CEOAdaptiveExecutionBridge(Path.home()/"companyos").run(
mission,validation,providers,history=history,strategy_history=[],strategy_attempt=1,execution_history=[]
)
print(json.dumps(result,indent=2,default=str))
