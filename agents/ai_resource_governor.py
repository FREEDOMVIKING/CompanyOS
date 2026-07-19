#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase25_bundle2_config.json"
PROV=MEM/"ai_provenance_log.json"
ROUTES=MEM/"ai_task_routing_plan.json"
OUT=MEM/"ai_resource_governor_report.json"
STATE=MEM/"ai_resource_governor_state.json"
HEALTH=MEM/"ai_resource_governor_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def run():
    cfg=load(CFG,{})
    events=load(PROV,{}).get("events",[])
    local=sum(1 for e in events if e.get("provider_used")=="local_llama_fallback")
    primary=sum(1 for e in events if e.get("provider_used")=="openai_primary")
    route_count=load(ROUTES,{}).get("route_count",0)
    payload={
      "generated_at":now(),
      "openai_completed":primary,
      "local_fallback_completed":local,
      "queued_routes":route_count,
      "maximum_parallel_specialists":cfg.get("maximum_parallel_specialists",3),
      "local_context_limit":cfg.get("local_model_context_limit",4096),
      "recommendation":"Prefer OpenAI when available; use local fallback for resilience and low-cost internal work.",
      "external_authority_granted":False
    }
    save(OUT,payload);save(STATE,{"last_run_at":now()});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"ai_resource_governor_complete","report":payload}

print(json.dumps(run(),indent=2))
