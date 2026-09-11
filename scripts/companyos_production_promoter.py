#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations
import json, sys, time
from pathlib import Path

ROOT=Path.home()/"companyos"
RT=ROOT/".companyos_runtime"
READY=RT/"production_readiness"
OUT=RT/"production_promotions"
STATE=RT/"production_promoter_state.json"

OUT.mkdir(parents=True,exist_ok=True)

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n")
    t.replace(p)

def promote():
    results=[]
    for p in sorted(READY.glob("*.json")):
        r=load(p,{})
        if not r.get("ready_for_production_promotion"):
            continue
        vid=r.get("venture_id")
        if not vid:
            continue

        rec={
            "venture_id":vid,
            "created_at":time.time(),
            "promotion_state":"prepared_for_production_gate",
            "service_activation_plan":{
                "status":"prepared",
                "health_check_required":True,
                "rollback_plan_required":True,
                "telemetry_required":True
            },
            "external_deployment_executed":False,
            "external_action_gate_required":True,
            "financial_action_gate_required":True
        }
        save(OUT/f"{vid}.json",rec)
        results.append(rec)

    out={
        "ok":True,
        "processed_at":time.time(),
        "promotions_prepared":len(results),
        "results":results
    }
    save(STATE,out)
    return out

cmd=sys.argv[1] if len(sys.argv)>1 else "status"
print(json.dumps(promote() if cmd=="promote" else load(STATE,{"ok":True,"status":"not_run"}),indent=2))
