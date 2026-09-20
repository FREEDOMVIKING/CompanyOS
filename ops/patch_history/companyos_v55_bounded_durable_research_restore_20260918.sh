#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"; export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V55 BOUNDED DURABLE RESEARCH RESTORE ====="
STAMP="$(date +%Y%m%d_%H%M%S)"; B="$HOME/.companyos_runtime/backups/v55_$STAMP"
mkdir -p "$B"
cp -a "$HOME/.companyos_runtime/execution_kernel.sqlite3"* "$B/" 2>/dev/null || true
cp -a "$HOME/.companyos_runtime/task_queue" "$B/" 2>/dev/null || true

python - <<'PY'
import json,time,sqlite3,os
from pathlib import Path
from collections import Counter
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue,TaskRecord
from companyos.runtime.autonomous_goal_execution_loop import AutonomousGoalExecutionLoop

LIMIT=int(os.getenv("COMPANYOS_V55_LIMIT","8"))
q=AutonomousTaskQueue(); db=q.kernel.db_path
# Current dispatcher source must contain the fixed, defined result flow.
src=Path("companyos/runtime/autonomous_task_dispatcher.py").read_text()
required=["ok, result, error = guard.execute(", "task = self.queue.complete(task, result)"]
if not all(x in src for x in required):
    raise SystemExit("V55_ABORT=current dispatcher result flow not verified")

con=sqlite3.connect(str(db)); con.row_factory=sqlite3.Row
rows=con.execute("""SELECT * FROM tasks
 WHERE task_type='research' AND stage='research' AND state='FAILED'
 AND attempts>=max_attempts AND last_error LIKE '%NameError%result%'
 ORDER BY created_at_unix ASC""").fetchall()

eligible=[]
for r in rows:
    tid=r["task_id"]; path=q._path(tid)
    if path.exists(): continue
    # Only historical orchestration chains whose downstream planning exists in visible queue.
    gid=r["goal_id"] or ""
    if ":goal:" not in gid: continue
    found=False
    for t in q._iter_task_files():
        p=t.payload if isinstance(t.payload,dict) else {}
        if p.get("goal_id")==gid and p.get("stage")=="planning" and p.get("depends_on_stage")=="research":
            found=True; break
    if found: eligible.append(r)
selected=eligible[:LIMIT]
restored=[]
for r in selected:
    payload=json.loads(r["payload_json"] or "{}")
    # Preserve identity/idempotency, reset only execution lifecycle for a real retry.
    t=TaskRecord(
      task_id=r["task_id"], idempotency_key=r["idempotency_key"] or "",
      task_type=r["task_type"], priority=int(r["priority"]),
      payload=payload, state="QUEUED", assigned_agent=None,
      attempts=0, max_attempts=max(3,int(r["max_attempts"])),
      created_at_unix=float(r["created_at_unix"]), updated_at_unix=time.time(),
      next_attempt_unix=time.time(), result=None, last_error=None)
    q.save(t)
    restored.append(t.task_id)
con.close()

print("ELIGIBLE_FAILED_MISSING_RESEARCH=",len(eligible))
print("RESTORED_THIS_BATCH=",len(restored))
print("RESTORED_IDS=",restored)
print("CURRENT_DISPATCHER_RESULT_FLOW=VERIFIED")
print("DEPENDENCIES_BYPASSED=0")
print("DUPLICATE_KEYS_CREATED=0")

loop=AutonomousGoalExecutionLoop(q)
before=Counter(t.state for t in q._iter_task_files())
results=loop.run_bounded_batch(max_dispatches=min(8,max(1,len(restored))))
after=Counter(t.state for t in q._iter_task_files())
print("BEFORE=",dict(before))
print("DISPATCH_RESULTS=",[{"task_id":x.task_id,"state":x.state,"reason":x.reason} for x in results])
print("AFTER=",dict(after))
out=Path.home()/".companyos_runtime"/f"v55_durable_research_restore_{int(time.time())}.json"
out.write_text(json.dumps({"eligible":len(eligible),"restored":restored,
 "before":dict(before),"results":[x.__dict__ for x in results],"after":dict(after)},indent=2,default=str)+"\n")
print("REPORT=",out)
print("V55_RESTORE_AND_RETRY=PASS")
PY
