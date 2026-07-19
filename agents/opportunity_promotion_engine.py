#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase23_bundle2_config.json"
SOURCE=MEM/"generated_business_opportunities.json"
QUEUE=MEM/"opportunity_promotion_queue.json"
STATE=MEM/"opportunity_promotion_state.json"
HEALTH=MEM/"opportunity_promotion_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def fid(x):return hashlib.sha256(json.dumps(x,sort_keys=True,default=str).encode()).hexdigest()[:20]

def promote():
    cfg=load(CFG,{})
    rows=load(SOURCE,{}).get("opportunities",[])
    old=load(QUEUE,{"items":[]}).get("items",[])
    seen={x.get("promotion_id") for x in old}
    maximum=int(cfg.get("maximum_promotions_per_cycle",10))
    added=[]
    for row in rows:
        if len(added)>=maximum:break
        pid=fid({"id":row.get("id"),"title":row.get("title")})
        if pid in seen:continue
        item={"promotion_id":pid,"opportunity_id":row.get("id"),"title":row.get("title"),
          "category":row.get("category"),"score":row.get("score"),
          "status":"ready_for_internal_review","authority":"internal_non_destructive_only",
          "created_at":now()}
        old.append(item);added.append(item);seen.add(pid)
    payload={"generated_at":now(),"item_count":len(old),"items":old}
    save(QUEUE,payload);save(STATE,{"last_promoted_at":now(),"added_count":len(added),"item_count":len(old)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"item_count":len(old)})
    return {"success":True,"status":"opportunity_promotion_complete","added_count":len(added),"queue":payload}

def status():
    return {"success":True,"status":"opportunity_promotion_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"queue":load(QUEUE,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=promote() if a=="promote" else status() if a=="status" else {"success":False,"allowed":["promote","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
