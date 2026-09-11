#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase24_bundle2_config.json"
PROJECTS=MEM/"project_execution_registry.json"
PROFILES=MEM/"specialist_performance_profiles.json"
OUT=MEM/"specialist_project_teams.json"
STATE=MEM/"specialist_team_state.json"
HEALTH=MEM/"specialist_team_health.json"

DEFAULT_ROLES=["research","analysis","planning","review","coordination"]

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def gid(x):return hashlib.sha256(str(x).encode()).hexdigest()[:16]

def build():
    cfg=load(CFG,{})
    projects=load(PROJECTS,{}).get("projects",[])
    profiles=load(PROFILES,{}).get("profiles",[])
    ranked=[p.get("specialist_role") for p in profiles if p.get("specialist_role")]
    roles=(ranked+DEFAULT_ROLES)
    teams=[]
    max_size=int(cfg.get("maximum_team_size",5))
    for p in projects:
        members=[]
        seen=set()
        for role in roles:
            if role in seen:continue
            members.append({"role":role,"assignment":"internal_specialist","status":"assigned"})
            seen.add(role)
            if len(members)>=max_size:break
        teams.append({
          "team_id":gid(p.get("project_id")),
          "project_id":p.get("project_id"),
          "project_title":p.get("title"),
          "member_count":len(members),
          "members":members,
          "status":"formed_for_internal_collaboration",
          "created_at":now()
        })
    payload={"generated_at":now(),"team_count":len(teams),"teams":teams}
    save(OUT,payload);save(STATE,{"last_built_at":now(),"team_count":len(teams)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"team_count":len(teams)})
    return {"success":True,"status":"specialist_team_build_complete","report":payload}

def status():
    return {"success":True,"status":"specialist_team_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=build() if a=="build" else status() if a=="status" else {"success":False,"allowed":["build","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
