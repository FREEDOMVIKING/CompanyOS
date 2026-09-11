#!/usr/bin/env python3
import json,sys,time
from pathlib import Path
RT=Path.home()/"companyos"/".companyos_runtime"
DIR=RT/"venture_directives"; OUT=RT/"launch_ready"; STATE=RT/"launch_readiness_state.json"
OUT.mkdir(parents=True,exist_ok=True)
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d): p.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n")
def assess():
    res=[]
    for p in sorted(DIR.glob("*.json")):
        d=load(p,{})
        vid=d.get("venture_id")
        if not vid: continue
        internal=bool(d.get("internal_execution_complete"))
        gate=any(isinstance(m,dict) and m.get("type")=="gate" and m.get("status")=="ready_for_policy_review" for m in d.get("milestones",[]))
        missing=d.get("missing_specialist_roles") or []
        blockers=[]
        if not internal: blockers.append("internal_execution_incomplete")
        if not gate: blockers.append("launch_gate_not_ready")
        if missing: blockers.append("missing_specialist_roles")
        x={"venture_id":vid,"assessed_at":time.time(),"ready_for_build":not blockers,
           "ready_for_external_launch":False,"blockers":blockers,
           "external_actions_require_existing_gate":True,
           "financial_actions_require_existing_gate":True}
        save(OUT/f"{vid}.json",x); res.append(x)
    out={"ok":True,"ventures_assessed":len(res),"ready_for_build":sum(1 for x in res if x["ready_for_build"]),"results":res}
    save(STATE,out); return out
cmd=sys.argv[1] if len(sys.argv)>1 else "status"
print(json.dumps(assess() if cmd=="assess" else load(STATE,{"ok":True,"status":"not_run"}),indent=2))
