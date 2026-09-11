#!/usr/bin/env python3
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
SOURCES=[MEM/"platform_architecture_plan.json",MEM/"sandbox_build_report.json",MEM/"self_test_report.json",MEM/"internal_promotion_report.json"]
OUT=MEM/"architecture_memory.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def run():
    mem=load(OUT,{"events":[]});seen={x["event_id"] for x in mem.get("events",[])}
    for p in SOURCES:
        d=load(p,{})
        if not d:continue
        eid=hashlib.sha256((p.name+"|"+str(d.get("generated_at"))).encode()).hexdigest()[:18]
        if eid not in seen:
            mem.setdefault("events",[]).append({"event_id":eid,"source":p.name,"captured_at":now(),"payload":d});seen.add(eid)
    mem["events"]=mem["events"][-1000:];mem["generated_at"]=now();mem["event_count"]=len(mem["events"])
    OUT.write_text(json.dumps(mem,indent=2))
    return {"success":True,"status":"architecture_memory_complete","event_count":mem["event_count"]}
print(json.dumps(run(),indent=2))
