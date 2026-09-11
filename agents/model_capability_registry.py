#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"model_capability_registry.json"
STATE=MEM/"model_capability_state.json"
HEALTH=MEM/"model_capability_health.json"
PROVIDER=MEM/"ai_provider_health_report.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def run():
    ph=load(PROVIDER,{})
    rows=[
      {
        "provider":"openai",
        "model":"gpt-4.1-mini",
        "available":bool(ph.get("primary",{}).get("configured")),
        "strengths":["reasoning","planning","structured_outputs","tool_orchestration"],
        "cost_class":"metered_api",
        "priority":1
      },
      {
        "provider":"local_llama",
        "model":"qwen2.5-1.5b-instruct-q4_k_m",
        "available":bool(ph.get("fallback",{}).get("reachable")),
        "strengths":["offline_reasoning","summarization","classification","fallback_execution"],
        "cost_class":"local_compute",
        "priority":2
      }
    ]
    payload={"generated_at":now(),"model_count":len(rows),"models":rows}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"model_count":len(rows)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"model_capability_registry_complete","registry":payload}

print(json.dumps(run(),indent=2))
