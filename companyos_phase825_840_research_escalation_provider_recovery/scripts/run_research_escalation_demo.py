#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase825_840 import CEOResearchEscalationBridge

root = Path.home() / "companyos"

mission = {
    "mission_id":"phase825_demo",
    "mission_type":"research",
    "attempts":0,
    "context":{
        "venture_id":"demo",
        "query_type":"market",
        "query":"contractor estimating software demand",
        "provider_hint":"github",
        "evidence":[],
    }
}

provider_results = {
    "github":{
        "success":False,
        "error":"HTTP Error 403: rate limit exceeded",
        "items":[],
    },
    "public_web":{
        "success":True,
        "items":[
            {"url":"a","source_class":"official","tags":["problem","risk"]},
            {"url":"b","source_class":"reputable_news","tags":["demand","alternatives"]},
            {"url":"c","source_class":"competitor_site","tags":["pricing"]},
        ],
    },
}

result = CEOResearchEscalationBridge(root).run(
    mission,
    provider_results=provider_results,
    max_total_attempts=6,
)
print(json.dumps(result, indent=2, default=str))
