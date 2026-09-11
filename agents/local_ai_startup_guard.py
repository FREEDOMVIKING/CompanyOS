#!/usr/bin/env python3
import json, subprocess, urllib.request, time
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"local_ai_startup_guard.json"; STATE=MEM/"local_ai_startup_guard_state.json"; HEALTH=MEM/"local_ai_startup_guard_health.json"
MODEL=Path.home()/"llama.cpp/models/qwen2.5-1.5b-instruct-q4_k_m.gguf"
SERVER=Path.home()/"llama.cpp/build/bin/llama-server"
LOG=ROOT/"logs/local_ai_server.log"

def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def reachable():
    try:
        urllib.request.urlopen("http://127.0.0.1:8080/health",timeout=3).read()
        return True
    except:return False

def run():
    started=False
    if not reachable() and SERVER.exists() and MODEL.exists():
        LOG.parent.mkdir(parents=True,exist_ok=True)
        with LOG.open("ab") as f:
            subprocess.Popen([str(SERVER),"-m",str(MODEL),"--host","127.0.0.1","--port","8080","-c","4096"],
                             stdout=f,stderr=f,start_new_session=True)
        started=True
        for _ in range(20):
            time.sleep(1)
            if reachable(): break
    ok=reachable()
    payload={"generated_at":now(),"reachable":ok,"started_by_guard":started,
             "model_exists":MODEL.exists(),"server_exists":SERVER.exists(),"port":8080}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"reachable":ok});save(HEALTH,{"healthy":ok,"last_checked_at":now()})
    return {"success":True,"status":"local_ai_startup_guard_complete","report":payload}

print(json.dumps(run(),indent=2))
