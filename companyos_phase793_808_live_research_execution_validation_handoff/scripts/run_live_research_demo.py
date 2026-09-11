#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase793_808 import CEOResearchExecutionBridge

root = Path.home() / "companyos"
mission = {
    "mission_id":"phase793_demo",
    "mission_type":"research",
    "priority":0.9,
    "attempts":0,
    "context":{
        "venture_id":"demo_venture",
        "query_type":"market",
        "query":"contractor estimating software demand",
        "provider_hint":"github",
        "provider_results":{
            "github":{"success":False,"error":"HTTP Error 403: rate limit exceeded","items":[]},
            "public_web":{"success":True,"items":[
                {"url":"a","source_class":"official","tags":["problem","risk"]},
                {"url":"b","source_class":"reputable_news","tags":["demand","alternatives"]},
                {"url":"c","source_class":"competitor_site","tags":["pricing"]},
            ]},
        },
    },
}
print(json.dumps(CEOResearchExecutionBridge(root).process(mission, {}), indent=2, default=str))
