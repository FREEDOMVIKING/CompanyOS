#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
STAMP="$(date +%Y%m%d_%H%M%S)"
BK=".companyos_runtime/backups/v26_${STAMP}"
mkdir -p "$BK" companyos/runtime scripts tests

echo "===== COMPANYOS V26 — BOUNDED BACKLOG CONTROL ====="
echo "Supervisor will NOT be restarted."

cp -f companyos/runtime/autonomous_task_queue.py "$BK/" 2>/dev/null || true
cp -f companyos/runtime/dependency_aware_dispatcher.py "$BK/" 2>/dev/null || true

cat > companyos/runtime/bounded_backlog_controller.py <<'PY'
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
PY

cat > scripts/companyos_backlogctl <<'PY'
#!/data/data/com.termux/files/usr/bin/python
import json, os, sys, time
from pathlib import Path
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.bounded_backlog_controller import select_bounded

q=AutonomousTaskQueue()
tasks=q.all_tasks()
terminal={"COMPLETED","FAILED","CANCELLED","HALTED"}
active=[t for t in tasks if str(getattr(t,"state","")).upper() not in terminal]
sel=select_bounded(tasks)
print(json.dumps({
 "total":len(tasks),
 "nonterminal":len(active),
 "batch_size":len(sel.selected),
 "scanned":sel.scanned,
 "eligible_scanned":sel.eligible,
 "scan_seconds":round(sel.elapsed,4),
 "selected":[{
   "task_id":getattr(t,"task_id",None),
   "state":getattr(t,"state",None),
   "priority":getattr(t,"priority",None),
   "stage":(getattr(t,"payload",{}) or {}).get("stage")
 } for t in sel.selected[:20]]
},indent=2))
PY
chmod +x scripts/companyos_backlogctl

cat > tests/test_bounded_backlog_controller.py <<'PY'
from types import SimpleNamespace
from companyos.runtime.bounded_backlog_controller import select_bounded

def t(i,stage="research",priority=100,state="QUEUED"):
    return SimpleNamespace(task_id=str(i),idempotency_key=str(i),state=state,
        priority=priority,created_at_unix=i,payload={"stage":stage})

def test_bounded():
    rows=[t(i) for i in range(5000)]
    x=select_bounded(rows,limit=25,scan_limit=200,budget_seconds=2)
    assert len(x.selected)==25
    assert x.scanned<=200

def test_execution_priority():
    rows=[t(1,"research",1),t(2,"execution",100)]
    x=select_bounded(rows,limit=2,scan_limit=10,budget_seconds=2)
    assert x.selected[0].task_id=="2"

def test_terminal_skipped():
    rows=[t(1,state="COMPLETED"),t(2)]
    x=select_bounded(rows,limit=10,scan_limit=10,budget_seconds=2)
    assert [z.task_id for z in x.selected]==["2"]
PY

echo "===== COMPILE ====="
python -m py_compile companyos/runtime/bounded_backlog_controller.py \
  companyos/runtime/autonomous_task_queue.py \
  companyos/runtime/dependency_aware_dispatcher.py
echo "COMPILE=PASS"

echo "===== TESTS ====="
python -m pytest -q tests/test_bounded_backlog_controller.py
echo "TESTS=PASS"

echo "===== LIVE QUEUE DRY RUN ====="
PYTHONPATH=. scripts/companyos_backlogctl

echo "===== SUPERVISOR PRESERVATION ====="
pgrep -af 'companyos.runtime.service_supervisor' || true

echo "===== INSTALL SAFE ENV DEFAULTS ====="
ENV="$HOME/.companyos_launch_env"
touch "$ENV"
chmod 600 "$ENV"
for kv in \
 'COMPANYOS_BACKLOG_BATCH_SIZE=32' \
 'COMPANYOS_BACKLOG_SCAN_LIMIT=1000' \
 'COMPANYOS_BACKLOG_SCAN_SECONDS=1.5'
do
  k="${kv%%=*}"
  grep -q "^${k}=" "$ENV" 2>/dev/null || echo "$kv" >> "$ENV"
done

echo "===== GIT: EXPLICIT FILES ONLY ====="
git add companyos/runtime/bounded_backlog_controller.py \
        scripts/companyos_backlogctl \
        tests/test_bounded_backlog_controller.py
git commit -m "Add V26 bounded backlog controller" || true
git push origin HEAD || true

echo
echo "COMPANYOS_V26_BOUNDED_BACKLOG_CONTROL=PASS"
echo "SUPERVISOR_RESTARTED=NO"
echo "BACKLOG_DELETED=NO"
echo "FINANCE_CONNECTORS_CHANGED=NO"
echo "Next: use the dry-run output to wire bounded selection into the exact live dispatcher call path."
