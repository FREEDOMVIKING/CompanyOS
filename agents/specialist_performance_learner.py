#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase23_bundle2_config.json"
RESULTS=MEM/"specialist_runtime_results.json"
OUT=MEM/"specialist_performance_profiles.json"
STATE=MEM/"specialist_learning_state.json"
HEALTH=MEM/"specialist_learning_health.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def f(v,d=0):
    try:return float(v)
    except:return float(d)

def learn():
    cfg=load(CFG,{})
    rows=load(RESULTS,{}).get("results",[])
    window=int(cfg.get("specialist_learning_window",200))
    minimum=f(cfg.get("minimum_confidence_for_learning",.5),.5)
    buckets=defaultdict(list)

    for r in rows[-window:]:
        if r.get("status")!="completed": continue
        actual=r.get("actual_result") or {}
        conf=f(actual.get("confidence",0),0)
        if conf<minimum: continue
        role=r.get("specialist_role") or r.get("action_type") or "general"
        buckets[role].append(conf)

    profiles=[]
    for role,vals in buckets.items():
        avg=sum(vals)/len(vals)
        profiles.append({
          "specialist_role":role,
          "samples":len(vals),
          "average_confidence":round(avg,3),
          "performance_band":"strong" if avg>=.8 else "good" if avg>=.65 else "developing"
        })
    profiles.sort(key=lambda x:(x["average_confidence"],x["samples"]),reverse=True)
    payload={"generated_at":now(),"profile_count":len(profiles),"profiles":profiles}
    save(OUT,payload);save(STATE,{"last_learned_at":now(),"profile_count":len(profiles)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"profile_count":len(profiles)})
    return {"success":True,"status":"specialist_performance_learning_complete","report":payload}

def status():
    return {"success":True,"status":"specialist_learning_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"profiles":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=learn() if a=="learn" else status() if a=="status" else {"success":False,"allowed":["learn","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
