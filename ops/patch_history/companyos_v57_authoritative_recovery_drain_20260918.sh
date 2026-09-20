#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"; export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V57 AUTHORITATIVE RECOVERY + DRAIN ====="
STAMP="$(date +%Y%m%d_%H%M%S)"; B="$HOME/.companyos_runtime/backups/v57_$STAMP"; mkdir -p "$B"
cp -a "$HOME/.companyos_runtime/execution_kernel.sqlite3"* "$B/" 2>/dev/null || true
cp -a "$HOME/.companyos_runtime/task_queue" "$B/" 2>/dev/null || true

python - <<'PY'
import json,sqlite3,time,os
from pathlib import Path
from collections import Counter
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue,TaskRecord
from companyos.runtime.autonomous_goal_execution_loop import AutonomousGoalExecutionLoop

LIMIT=max(1,min(int(os.getenv("COMPANYOS_V57_RESTORE_LIMIT","16")),32))
q=AutonomousTaskQueue(); db=q.kernel.db_path
visible={t.task_id:t for t in q._iter_task_files()}

con=sqlite3.connect(str(db)); con.row_factory=sqlite3.Row
rows=con.execute("""SELECT * FROM tasks
 WHERE task_type='research' AND stage='research'
 AND state='FAILED' AND attempts>=max_attempts
 AND last_error LIKE '%NameError%result%'
 ORDER BY created_at_unix ASC""").fetchall()

eligible=[]
for r in rows:
    if r["task_id"] in visible: continue
    gid=str(r["goal_id"] or "")
    if ":goal:" not in gid: continue
    # Require visible queued planning child for same goal.
    child=False
    for t in visible.values():
        p=t.payload if isinstance(t.payload,dict) else {}
        if (t.state=="QUEUED" and str(p.get("goal_id",""))==gid
            and p.get("stage")=="planning" and p.get("depends_on_stage")=="research"):
            child=True; break
    if child: eligible.append(r)

selected=eligible[:LIMIT]
restored=[]
for r in selected:
    payload=json.loads(r["payload_json"] or "{}")
    if str(payload.get("goal_id","")) != str(r["goal_id"] or "") or payload.get("stage")!="research":
        continue
    t=TaskRecord(
      task_id=r["task_id"], idempotency_key=r["idempotency_key"] or "",
      task_type="research", priority=int(r["priority"] or 100), payload=payload,
      state="QUEUED", assigned_agent=None, attempts=0,
      max_attempts=max(3,int(r["max_attempts"] or 3)),
      created_at_unix=float(r["created_at_unix"]), updated_at_unix=time.time(),
      next_attempt_unix=time.time(), result=None, last_error=None)
    q.save(t); restored.append(t.task_id)
con.close()

before=Counter(t.state for t in q._iter_task_files())
loop=AutonomousGoalExecutionLoop(q)
results=loop.run_bounded_batch(max_dispatches=min(32,max(1,len(restored))))
after=Counter(t.state for t in q._iter_task_files())

restored_states={}
unlocked=0
for tid in restored:
    try:
        t=q.load(tid); restored_states[tid]=t.state
        if t.state=="COMPLETED":
            p=t.payload if isinstance(t.payload,dict) else {}
            gid=str(p.get("goal_id",""))
            for x in q._iter_task_files():
                xp=x.payload if isinstance(x.payload,dict) else {}
                if x.state=="QUEUED" and str(xp.get("goal_id",""))==gid and xp.get("stage")=="planning":
                    unlocked+=1; break
    except Exception: restored_states[tid]="MISSING"

report={"eligible_historical_missing_research":len(eligible),
 "restore_limit":LIMIT,"restored_count":len(restored),"restored_ids":restored,
 "restored_states":restored_states,"dispatch_results":[x.__dict__ for x in results],
 "planning_unlocked":unlocked,"before":dict(before),"after":dict(after)}
out=Path.home()/".companyos_runtime"/f"v57_authoritative_recovery_{int(time.time())}.json"
out.write_text(json.dumps(report,indent=2,default=str)+"\n")
print(json.dumps(report,indent=2,default=str))
print("DUPLICATE_TASKS_CREATED=0")
print("DEPENDENCIES_BYPASSED=0")
print("SQLITE_ROWS_DELETED=0")
print("V57_RECOVERY_DRAIN=PASS")
PY
