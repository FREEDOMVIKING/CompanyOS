#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase937_1000 import CEOSupercycleController

mission={
 "mission_id":"phase1000_demo_validation",
 "mission_type":"validation",
 "context":{
  "venture_id":"demo_venture",
  "query":"contractor estimating software demand",
  "research_confidence":.86,
  "research_packet":{
   "confidence":.86,
   "evidence":[
    {"id":"1","source_class":"official","tags":["problem","pricing"],"willingness_to_pay_score":1.0},
    {"id":"2","source_class":"official","tags":["problem","demand"]},
    {"id":"3","source_class":"reputable_news","tags":["demand","alternatives"]},
    {"id":"4","source_class":"competitor_site","tags":["pricing","alternatives"],"willingness_to_pay_score":.9},
    {"id":"5","source_class":"public_web","tags":["problem","demand","pricing"],"willingness_to_pay_score":.8}
   ]
  }
 }
}

validation={
 "decision":"REVISE",
 "scores":{"research_confidence":.86,"validation_confidence":.65},
 "false_positive_guard":{"passed":True},
 "contradictions":{"resolved":True,"topics":[]}
}

result=CEOSupercycleController(Path.home()/"companyos").run(
    mission,
    validation,
    provider_results={},
    max_research_rounds=2,
    build_result={"success":True},
    test_results=[{"name":"core","passed":True},{"name":"integration","passed":True}],
    safety_checks=[{"name":"secrets","passed":True},{"name":"rollback","passed":True}],
)
print(json.dumps(result,indent=2,default=str))
