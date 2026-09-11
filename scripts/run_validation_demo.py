#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase841_856 import CEOValidationRuntimeBridge

root=Path.home()/"companyos"
mission={
    "mission_id":"phase841_demo_validation",
    "mission_type":"validation",
    "attempts":0,
    "context":{
        "venture_id":"demo_venture",
        "research_confidence":0.82,
        "research_packet":{
            "confidence":0.82,
            "contradictions":{"topics":[]},
            "evidence":[
                {"id":"1","source_class":"official","tags":["problem","risk"]},
                {"id":"2","source_class":"reputable_news","tags":["demand","alternatives"]},
                {"id":"3","source_class":"competitor_site","tags":["pricing"],"willingness_to_pay_score":1.0},
                {"id":"4","source_class":"official","tags":["problem","demand"]},
                {"id":"5","source_class":"public_web","tags":["pricing","alternatives"],"willingness_to_pay_score":0.8},
            ]
        }
    }
}
print(json.dumps(CEOValidationRuntimeBridge(root).run(mission),indent=2,default=str))
