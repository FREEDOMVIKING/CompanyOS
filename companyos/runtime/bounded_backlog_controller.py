from __future__ import annotations
import os, time
from dataclasses import dataclass
from typing import Any

TERMINAL={"COMPLETED","FAILED","CANCELLED","HALTED"}
STAGE_RANK={
    "execution":0,"execute":0,"launch":1,"validation":2,"experiment":2,
    "sales":2,"build":3,"planning":4,"research":5,"":6
}

@dataclass
class BacklogSelection:
    selected:list[Any]
    scanned:int
    eligible:int
    elapsed:float

def _payload(t):
    p=getattr(t,"payload",None)
    return p if isinstance(p,dict) else {}

def _priority(t):
    try: return int(getattr(t,"priority",100))
    except Exception: return 100

def _rank(t):
    p=_payload(t)
    stage=str(p.get("stage") or p.get("depends_on_stage") or "").lower()
    profit=bool(p.get("profit_ready") or p.get("execution_ready") or
                p.get("selected_action") or p.get("action_packet_id"))
    return (0 if profit else 1, STAGE_RANK.get(stage,5), _priority(t),
            float(getattr(t,"created_at_unix",0) or 0))

def select_bounded(tasks, limit=None, scan_limit=None, budget_seconds=None):
    limit=max(1,int(limit or os.getenv("COMPANYOS_BACKLOG_BATCH_SIZE","32")))
    scan_limit=max(limit,int(scan_limit or os.getenv("COMPANYOS_BACKLOG_SCAN_LIMIT","1000")))
    budget=float(budget_seconds or os.getenv("COMPANYOS_BACKLOG_SCAN_SECONDS","1.5"))
    started=time.monotonic()
    candidates=[]
    scanned=0
    seen=set()

    # Newest records first avoids repeatedly chewing through ancient backlog.
    for t in reversed(list(tasks)):
        if scanned >= scan_limit or time.monotonic()-started >= budget:
            break
        scanned += 1
        if str(getattr(t,"state","")).upper() in TERMINAL:
            continue
        key=str(getattr(t,"idempotency_key","") or getattr(t,"task_id",""))
        if key and key in seen:
            continue
        if key: seen.add(key)
        candidates.append(t)

    candidates.sort(key=_rank)
    return BacklogSelection(candidates[:limit],scanned,len(candidates),
                            time.monotonic()-started)
