#!/usr/bin/env python3
import json
from companyos_phase745_760 import ResearchQualityRuntime, CEOResearchSummary
providers=[
 {"name":"github","availability":0.4,"recent_failures":2,"cooldown_active":True},
 {"name":"public_web","availability":0.95,"recent_failures":0,"cooldown_active":False},
]
evidence=[
 {"id":"1","source_class":"official","authoritative":True,"tags":["problem","risk"]},
 {"id":"2","source_class":"reputable_news","tags":["demand","alternatives"]},
 {"id":"3","source_class":"competitor_site","tags":["pricing"]},
]
packet=ResearchQualityRuntime().run(providers,evidence,[])
print(json.dumps(packet,indent=2))
print(json.dumps(CEOResearchSummary().build(packet),indent=2))
