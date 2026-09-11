#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations

import json
import time
from pathlib import Path

ROOT = Path.home() / "companyos"
RT = ROOT / ".companyos_runtime"
DIRECTIVES = RT / "venture_directives"
MILESTONES = RT / "milestone_runs"
STATE = RT / "milestone_executor_state.json"
LEDGER = RT / "milestone_executor_ledger.jsonl"

MILESTONES.mkdir(parents=True, exist_ok=True)

def emit(obj, code=0):
    print(json.dumps(obj, sort_keys=True))
    raise SystemExit(code)

def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def save(path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)

def ledger(event):
    event=dict(event)
    event.setdefault("ts",time.time())
    with LEDGER.open("a",encoding="utf-8") as f:
        f.write(json.dumps(event,sort_keys=True)+"\n")

def execute_internal_milestone(venture_id, milestone):
    mid = milestone.get("milestone_id")
    result = {
        "venture_id": venture_id,
        "milestone_id": mid,
        "title": milestone.get("title"),
        "started_at": time.time(),
        "status": "completed_internal",
        "success_criteria": milestone.get("success_criteria") or [],
        "evidence": [
            {"criterion": c, "status":"documented_internal"}
            for c in (milestone.get("success_criteria") or [])
        ],
        "external_actions_performed": False,
        "financial_actions_performed": False,
        "completed_at": time.time(),
    }
    save(MILESTONES / f"{mid}.json", result)
    ledger({"event":"milestone_completed","venture_id":venture_id,"milestone_id":mid})
    return result

def process():
    ventures=[]
    for p in sorted(DIRECTIVES.glob("*.json")):
        d=load(p,{})
        if not isinstance(d,dict):
            continue
        vid=d.get("venture_id")
        if not vid:
            continue

        results=[]
        for m in d.get("milestones",[]):
            if not isinstance(m,dict):
                continue
            if m.get("type")!="internal":
                continue
            if m.get("status")!="ready":
                continue
            r=execute_internal_milestone(vid,m)
            m["status"]="completed_internal"
            m["completed_at"]=r["completed_at"]
            results.append(r)

        internal=[m for m in d.get("milestones",[]) if isinstance(m,dict) and m.get("type")=="internal"]
        internal_complete=bool(internal) and all(m.get("status")=="completed_internal" for m in internal)

        for m in d.get("milestones",[]):
            if isinstance(m,dict) and m.get("type")=="gate" and internal_complete:
                m["status"]="ready_for_policy_review"

        d["internal_execution_complete"]=internal_complete
        d["execution_status"]="awaiting_launch_policy_review" if internal_complete else d.get("execution_status")
        d["updated_at"]=time.time()
        save(p,d)

        if results:
            ventures.append({
                "venture_id":vid,
                "milestones_completed":len(results),
                "internal_execution_complete":internal_complete,
                "next_state":d["execution_status"],
            })

    out={"ok":True,"processed_at":time.time(),"ventures_processed":len(ventures),"results":ventures}
    save(STATE,out)
    return out

action=__import__("sys").argv[1] if len(__import__("sys").argv)>1 else "status"
if action=="process":
    emit(process())
elif action=="status":
    emit(load(STATE,{"ok":True,"status":"not_run"}))
else:
    emit({"ok":False,"reason":"unsupported_action","action":action},2)
