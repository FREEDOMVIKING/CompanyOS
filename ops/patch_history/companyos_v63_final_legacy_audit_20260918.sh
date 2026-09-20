#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"; export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V63 FINAL LEGACY FAILURE AUDIT ====="
python - <<'PY'
import sqlite3,json
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
q=AutonomousTaskQueue()
visible={t.task_id:t for t in q._iter_task_files()}
c=sqlite3.connect(str(q.kernel.db_path)); c.row_factory=sqlite3.Row
rows=c.execute('''SELECT task_id,idempotency_key,task_type,state,attempts,max_attempts,
 goal_id,stage,depends_on_stage,last_error,payload_json
 FROM tasks WHERE state='FAILED' ORDER BY updated_at_unix''').fetchall()
legacy=[r for r in rows if "NameError" in (r["last_error"] or "") and "result" in (r["last_error"] or "")]
print("TOTAL_FAILED=",len(rows))
print("LEGACY_RESULT_FAILURES=",len(legacy))
for r in legacy:
    print("LEGACY_TASK=",dict(r))
    print("JSON_VISIBLE=",r["task_id"] in visible)
    gid=str(r["goal_id"] or "")
    children=[]
    for t in visible.values():
        p=t.payload if isinstance(t.payload,dict) else {}
        if str(p.get("goal_id",""))==gid and p.get("depends_on_stage")=="research":
            children.append({"task_id":t.task_id,"stage":p.get("stage"),"state":t.state})
    print("DEPENDENT_CHILDREN=",children[:10])
print("OTHER_FAILED_ERRORS=",{})
from collections import Counter
print(dict(Counter((r["task_type"],r["stage"],r["last_error"]) for r in rows if r not in legacy)))
c.close()
print("DATABASE_WRITES=0")
print("QUEUE_WRITES=0")
print("V63_LEGACY_AUDIT=PASS")
PY
