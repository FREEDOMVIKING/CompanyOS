#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
RUNTIME=MEM/"specialist_runtime_config.json"
CONSUMER=MEM/"live_specialist_consumer_report.json"
OUT=MEM/"provider_health_report.json"
STATE=MEM/"provider_health_state.json"
HEALTH=MEM/"provider_health_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def evaluate():
    runtime=load(RUNTIME,{})
    report=load(CONSUMER,{})
    pending=int(report.get("pending_count",0) or 0)
    completed=int(report.get("completed_count",0) or 0)
    provider=runtime.get("provider","openai_compatible")
    model=runtime.get("model","openrouter/free")
    state="healthy" if pending==0 else "degraded" if completed>0 else "watch"
    payload={"generated_at":now(),"provider":provider,"model":model,
      "completed_count":completed,"pending_count":pending,"provider_state":state,
      "recommended_model":model}
    save(OUT,payload);save(STATE,{"last_evaluated_at":now(),"provider_state":state})
    save(HEALTH,{"healthy":state!="watch","last_checked_at":now(),"provider_state":state})
    return {"success":True,"status":"provider_health_evaluation_complete","report":payload}

def status():
    return {"success":True,"status":"provider_health_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=evaluate() if a=="evaluate" else status() if a=="status" else {"success":False,"allowed":["evaluate","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
