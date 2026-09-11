#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations
import json, sys, time
from pathlib import Path

ROOT=Path.home()/"companyos"
RT=ROOT/".companyos_runtime"
PROMO=RT/"production_promotions"
PLANS=RT/"execution_plans"
OUT=RT/"revenue_ops"
STATE=RT/"revenue_operations_state.json"

OUT.mkdir(parents=True,exist_ok=True)

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n")
    t.replace(p)

def build():
    results=[]
    for p in sorted(PROMO.glob("*.json")):
        promo=load(p,{})
        vid=promo.get("venture_id")
        if not vid:
            continue
        plan=load(PLANS/f"{vid}.json",{})
        title=plan.get("title") or vid

        rec={
            "venture_id":vid,
            "generated_at":time.time(),
            "venture_name":title,
            "customer_acquisition_workflow":{
                "status":"prepared",
                "stages":["lead_capture","qualification","offer","follow_up","conversion_tracking"]
            },
            "revenue_tracking":{
                "status":"prepared",
                "metrics":["leads","qualified_leads","conversions","gross_revenue","refunds","net_revenue"]
            },
            "customer_success_workflow":{
                "status":"prepared",
                "stages":["onboarding","delivery","health_check","support","retention"]
            },
            "pricing_execution":{
                "status":"planning_only",
                "automatic_charges_enabled":False
            },
            "external_messages_sent":False,
            "payments_collected":False,
            "financial_actions_performed":False
        }
        save(OUT/f"{vid}.json",rec)
        results.append(rec)

    out={
        "ok":True,
        "generated_at":time.time(),
        "ventures_prepared":len(results),
        "results":results
    }
    save(STATE,out)
    return out

cmd=sys.argv[1] if len(sys.argv)>1 else "status"
print(json.dumps(build() if cmd=="build" else load(STATE,{"ok":True,"status":"not_run"}),indent=2))
