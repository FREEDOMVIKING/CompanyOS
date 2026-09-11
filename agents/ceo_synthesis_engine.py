#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
VALID=MEM/"validated_ai_results.json"
RUNTIME=MEM/"specialist_runtime_results.json"
OUT=MEM/"ceo_ai_synthesis.json"
STATE=MEM/"ceo_ai_synthesis_state.json"
HEALTH=MEM/"ceo_ai_synthesis_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def run():
    valid_ids={x.get("work_id") for x in load(VALID,{}).get("results",[]) if x.get("valid")}
    summaries=[];recommendations=[];risks=[];providers={}
    for r in load(RUNTIME,{}).get("results",[]):
        if r.get("work_id") not in valid_ids: continue
        a=r.get("actual_result",{})
        if not isinstance(a,dict): continue
        if a.get("summary"):summaries.append(a["summary"])
        recommendations.extend(a.get("recommendations",[]) if isinstance(a.get("recommendations",[]),list) else [])
        risks.extend(a.get("risks",[]) if isinstance(a.get("risks",[]),list) else [])
        p=a.get("_provider_used","unknown");providers[p]=providers.get(p,0)+1
    payload={
      "generated_at":now(),
      "validated_input_count":len(valid_ids),
      "executive_summary":summaries[:10],
      "top_recommendations":recommendations[:15],
      "top_risks":risks[:15],
      "provider_mix":providers,
      "decision_boundary":"internal_recommendation_only",
      "external_authority_granted":False
    }
    save(OUT,payload);save(STATE,{"last_run_at":now(),"validated_input_count":len(valid_ids)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"ceo_ai_synthesis_complete","synthesis":payload}

print(json.dumps(run(),indent=2))
