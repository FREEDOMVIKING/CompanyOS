#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations
import json, sys, time
from pathlib import Path

ROOT=Path.home()/"companyos"
RT=ROOT/".companyos_runtime"
OPS=RT/"operations"
REV=RT/"revenue_ops"
OUT=RT/"portfolio_feedback"
STATE=RT/"portfolio_feedback_state.json"

OUT.mkdir(parents=True,exist_ok=True)

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n")
    t.replace(p)

def run():
    vids=set(p.stem for p in REV.glob("*.json")) | set(p.stem for p in OPS.glob("*.json"))
    results=[]
    for vid in sorted(vids):
        op=load(OPS/f"{vid}.json",{})
        rev=load(REV/f"{vid}.json",{})

        lifecycle=op.get("lifecycle_state","unknown")
        score=0
        if lifecycle=="operational_healthy": score+=3
        if lifecycle=="awaiting_existing_launch_gate": score+=1
        if op.get("rollback_recommended"): score-=2
        if rev: score+=1

        rec={
            "venture_id":vid,
            "evaluated_at":time.time(),
            "portfolio_signal_score":score,
            "lifecycle_state":lifecycle,
            "recommended_ceo_action":
                "scale_candidate" if score>=4 else
                "continue_validation" if score>=1 else
                "repair_or_pause",
            "automatic_spending_authorized":False
        }
        save(OUT/f"{vid}.json",rec)
        results.append(rec)

    out={
        "ok":True,
        "evaluated_at":time.time(),
        "ventures_evaluated":len(results),
        "results":results
    }
    save(STATE,out)
    return out

cmd=sys.argv[1] if len(sys.argv)>1 else "status"
print(json.dumps(run() if cmd=="run" else load(STATE,{"ok":True,"status":"not_run"}),indent=2))
