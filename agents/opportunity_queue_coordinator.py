#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"

CFG=MEM/"opportunity_queue_config.json"
SOURCE=MEM/"opportunity_action_queue.json"
ELIGIBILITY=MEM/"execution_eligibility_report.json"

STATE=MEM/"opportunity_queue_state.json"
REPORT=MEM/"opportunity_queue_report.json"
HEALTH=MEM/"opportunity_queue_health.json"
READY_QUEUE=MEM/"opportunity_ready_queue.json"

def now(): return datetime.now(timezone.utc).isoformat()

def load(path:Path, default:Any)->Any:
    try:return json.loads(path.read_text(encoding="utf-8"))
    except:return default

def save(path:Path, data:Any)->None:
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(data,indent=2),encoding="utf-8")
    tmp.replace(path)

def coordinate():
    cfg=load(CFG,{})
    source=load(SOURCE,{})
    eligibility=load(ELIGIBILITY,{})
    system_ready=eligibility.get("system_ready") is True
    matrix=eligibility.get("eligibility",{})

    minimum=float(cfg.get("minimum_priority",40))
    maximum=int(cfg.get("maximum_actions_per_cycle",10))

    ready=[]
    blocked=[]

    for item in source.get("actions",[])[:maximum]:
        try: priority=float(item.get("priority",50))
        except: priority=50.0
        category=item.get("category","internal_read_only")

        if priority < minimum:
            blocked.append({**item,"reason":"below_minimum_priority"})
            continue

        if cfg.get("require_system_ready",True) and not system_ready:
            blocked.append({**item,"reason":"system_not_ready"})
            continue

        if cfg.get("require_execution_eligibility",True) and not bool(matrix.get(category,False)):
            blocked.append({**item,"reason":"category_not_eligible"})
            continue

        ready.append({
            **item,
            "status":"ready",
            "queued_at":now()
        })

    ready.sort(key=lambda x: float(x.get("priority",0)), reverse=True)

    save(READY_QUEUE,{
        "generated_at":now(),
        "system_ready":system_ready,
        "actions":ready
    })

    report={
        "generated_at":now(),
        "system_ready":system_ready,
        "ready_count":len(ready),
        "blocked_count":len(blocked),
        "ready_actions":ready,
        "blocked_actions":blocked,
        "automatic_external_write":False,
        "automatic_customer_contact":False,
        "automatic_publication":False,
        "automatic_spending":False,
        "automatic_code_changes":False,
        "automatic_merge":False,
        "automatic_deploy":False,
        "automatic_destructive_actions":False
    }

    save(REPORT,report)
    save(STATE,{
        "last_coordinated_at":now(),
        "system_ready":system_ready,
        "ready_count":len(ready),
        "blocked_count":len(blocked),
        "top_action":ready[0]["title"] if ready else None
    })
    save(HEALTH,{
        "healthy":True,
        "last_checked_at":now(),
        "ready_count":len(ready),
        "blocked_count":len(blocked)
    })

    return {
        "success":True,
        "status":"opportunity_queue_coordination_complete",
        "report":report
    }

def status():
    return {
        "success":True,
        "status":"opportunity_queue_status",
        "state":load(STATE,{}),
        "health":load(HEALTH,{}),
        "report":load(REPORT,{}),
        "queue":load(READY_QUEUE,{})
    }

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=coordinate() if a=="coordinate" else status() if a=="status" else {"success":False,"allowed":["coordinate","status"]}
print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
