from __future__ import annotations
import json, collections, time
from pathlib import Path

def probe(root=None):
    root=Path(root or (Path.home()/".companyos_runtime"/"task_queue"))
    rows=[]; bad=0
    for p in root.iterdir() if root.exists() else []:
        if p.suffix!=".json": continue
        try: rows.append(json.loads(p.read_text()))
        except Exception: bad+=1
    states=collections.Counter(str(x.get("state","UNKNOWN")).upper() for x in rows)
    types=collections.Counter(str(x.get("task_type") or x.get("type") or "UNKNOWN") for x in rows if str(x.get("state","")).upper()=="QUEUED")
    completed={(str(x.get("goal_id","")),str(x.get("stage") or x.get("task_type") or x.get("type") or "")) for x in rows if str(x.get("state","")).upper()=="COMPLETED"}
    reasons=collections.Counter(); ready=[]
    for x in rows:
        if str(x.get("state","")).upper()!="QUEUED": continue
        typ=str(x.get("task_type") or x.get("type") or "")
        dep=x.get("depends_on_stage")
        goal=str(x.get("goal_id",""))
        attempts=int(x.get("attempts",0) or 0)
        maxa=int(x.get("max_attempts",3) or 3)
        if attempts>=maxa: reasons["attempts_exhausted"]+=1
        elif dep and (goal,str(dep)) not in completed: reasons["dependency_blocked"]+=1
        elif typ not in {"research","planning","build"}: reasons["unsupported_type"]+=1
        else:
            reasons["execution_ready"]+=1
            if len(ready)<100: ready.append(str(x.get("task_id") or x.get("id") or ""))
    return {"states":dict(states),"queued_types":dict(types),"reasons":dict(reasons),"unreadable":bad,"ready_sample":ready,"ts":time.time()}
if __name__=="__main__": print(json.dumps(probe(),indent=2,sort_keys=True))
