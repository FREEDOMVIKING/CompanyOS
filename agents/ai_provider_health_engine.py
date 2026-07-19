#!/usr/bin/env python3
import json, os, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase25_bundle1_config.json"
OUT=MEM/"ai_provider_health_report.json"
STATE=MEM/"ai_provider_health_state.json"
HEALTH=MEM/"ai_provider_health_health.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(d,indent=2)); t.replace(p)

def http_ok(url, timeout):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return True, getattr(r,"status",200)
    except urllib.error.HTTPError as e:
        return False, e.code
    except Exception as e:
        return False, type(e).__name__

def run():
    cfg=load(CFG,{})
    timeout=int(cfg.get("provider_timeout_seconds",20))
    openai_key=bool(os.getenv("OPENAI_API_KEY","").strip())
    local_ok, local_status=http_ok(cfg.get("local_health_url","http://127.0.0.1:8080/health"), timeout)
    payload={
      "generated_at":now(),
      "primary":{"provider":"openai","configured":openai_key,"usable":openai_key,
                 "note":"Quota/HTTP health is validated during actual requests."},
      "fallback":{"provider":"local_llama","configured":True,"reachable":local_ok,
                  "status":local_status,"base_url":cfg.get("fallback_base_url")},
      "routing_policy":cfg.get("routing_policy"),
      "healthy": bool(openai_key or local_ok)
    }
    save(OUT,payload); save(STATE,{"last_run_at":now(),"healthy":payload["healthy"]})
    save(HEALTH,{"healthy":payload["healthy"],"last_checked_at":now()})
    return {"success":True,"status":"ai_provider_health_complete","report":payload}

print(json.dumps(run(),indent=2))
