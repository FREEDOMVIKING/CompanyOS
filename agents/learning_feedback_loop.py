#!/usr/bin/env python3
import json,statistics
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory";VALID=MEM/"validated_ai_results.json";PROV=MEM/"ai_provenance_log.json";OUT=MEM/"learning_feedback_report.json";STATE=MEM/"learning_feedback_state.json";HEALTH=MEM/"learning_feedback_health.json"
def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def run():
    vals=load(VALID,{}).get("results",[]);conf=[float(x.get("confidence",0) or 0) for x in vals if isinstance(x.get("confidence"),(int,float))];valid=sum(1 for x in vals if x.get("valid"));review=sum(1 for x in vals if not x.get("valid"));prov=load(PROV,{}).get("events",[]);mix={}
    for e in prov:
        p=e.get("provider_used","unknown");mix[p]=mix.get(p,0)+1
    lessons=[]
    if review>valid:lessons.append("Increase evidence quality and prompt specificity before synthesis.")
    if mix.get("local_llama_fallback",0)>0:lessons.append("Local fallback is functioning and should remain available for resilience.")
    if conf and statistics.mean(conf)<.65:lessons.append("Average confidence is below target; strengthen validation before promotion.")
    payload={"generated_at":now(),"validated_count":valid,"review_count":review,"average_confidence":round(statistics.mean(conf),3) if conf else None,"provider_mix":mix,"lessons":lessons,"learning_boundary":"internal_memory_only"}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"lesson_count":len(lessons)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"learning_feedback_complete","report":payload}
print(json.dumps(run(),indent=2))
