#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase24_config.json"
RESULTS=MEM/"specialist_runtime_results.json"
OUT=MEM/"specialist_collaboration_groups.json"
STATE=MEM/"specialist_collaboration_state.json"
HEALTH=MEM/"specialist_collaboration_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def gid(key):return hashlib.sha256(str(key).encode()).hexdigest()[:16]

def build():
    cfg=load(CFG,{})
    rows=load(RESULTS,{}).get("results",[])
    groups=defaultdict(list)
    for r in rows:
        if r.get("status")!="completed":continue
        key=r.get("opportunity_id") or r.get("plan_id") or "general"
        groups[key].append(r)
    out=[]
    for key,items in list(groups.items())[:int(cfg.get("maximum_collaboration_groups",10))]:
        summaries=[];recommendations=[];risks=[]
        for r in items:
            a=r.get("actual_result") or {}
            if a.get("summary"):summaries.append(a.get("summary"))
            recommendations+=a.get("recommendations",[]) or []
            risks+=a.get("risks",[]) or []
        out.append({
          "group_id":gid(key),"topic_id":key,"member_result_count":len(items),
          "combined_summaries":summaries[:10],
          "combined_recommendations":recommendations[:20],
          "combined_risks":risks[:20],
          "status":"ready_for_internal_synthesis",
          "created_at":now()
        })
    payload={"generated_at":now(),"group_count":len(out),"groups":out}
    save(OUT,payload);save(STATE,{"last_built_at":now(),"group_count":len(out)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"group_count":len(out)})
    return {"success":True,"status":"specialist_collaboration_complete","report":payload}

def status():
    return {"success":True,"status":"specialist_collaboration_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=build() if a=="build" else status() if a=="status" else {"success":False,"allowed":["build","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
