#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase777_792 import CEOMultiProviderBridge

root=Path.home()/"companyos"
mission={"mission_id":"demo_multi_provider","context":{"venture_id":"demo"}}
providers=[
 {"name":"github","availability":0.2,"recent_failures":2},
 {"name":"public_web","availability":1.0},
 {"name":"hacker_news","availability":0.9},
]
context={
 "provider_results":{
  "github":{"success":False,"error":"HTTP Error 403: rate limit exceeded","items":[]},
  "public_web":{"success":True,"items":[
   {"url":"a","source_class":"official","tags":["problem","risk"]},
   {"url":"b","source_class":"reputable_news","tags":["demand","alternatives"]},
   {"url":"c","source_class":"competitor_site","tags":["pricing"]},
  ]},
 }
}
result=CEOMultiProviderBridge(root).execute(
 mission,"contractor estimating software demand","market","github",providers,context
)
print(json.dumps(result,indent=2))
