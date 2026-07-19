#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase25_bundle2_config.json"
SRC=MEM/"specialist_runtime_results.json"
OUT=MEM/"validated_ai_results.json"
STATE=MEM/"result_validation_state.json"
HEALTH=MEM/"result_validation_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def run():
    minimum=float(load(CFG,{}).get("minimum_validation_confidence",0.55))
    rows=[]
    for r in load(SRC,{}).get("results",[]):
        actual=r.get("actual_result",{})
        if not isinstance(actual,dict): continue
        raw_confidence = actual.get("confidence", 0)

        if isinstance(raw_confidence, str):
            confidence_map = {
                "very_low": 0.2,
                "low": 0.3,
                "medium": 0.5,
                "moderate": 0.5,
                "high": 0.8,
                "very_high": 0.95
            }
            try:
                confidence = float(raw_confidence)
            except ValueError:
                confidence = confidence_map.get(
                    raw_confidence.strip().lower().replace(" ", "_"),
                    0.0
                )
        else:
            try:
                confidence = float(raw_confidence or 0)
            except (TypeError, ValueError):
                confidence = 0.0

        confidence = max(0.0, min(1.0, confidence))
        valid=bool(actual.get("summary")) and confidence>=minimum
        rows.append({
          "work_id":r.get("work_id"),
          "valid":valid,
          "confidence":confidence,
          "provider_used":actual.get("_provider_used","unknown"),
          "summary_present":bool(actual.get("summary")),
          "status":"validated_internal_result" if valid else "needs_internal_review",
          "execution_boundary":"internal_non_destructive_only"
        })
    payload={"generated_at":now(),"validated_count":sum(1 for x in rows if x["valid"]),
             "review_count":sum(1 for x in rows if not x["valid"]),"results":rows}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"result_count":len(rows)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"result_validation_complete","report":payload}

print(json.dumps(run(),indent=2))
