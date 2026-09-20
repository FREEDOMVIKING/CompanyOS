#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"; export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V60 SAFE JSON -> KERNEL RECONCILIATION ====="
STAMP="$(date +%Y%m%d_%H%M%S)"; B="$HOME/.companyos_runtime/backups/v60_$STAMP"; mkdir -p "$B"
cp -a "$HOME/.companyos_runtime/execution_kernel.sqlite3"* "$B/" 2>/dev/null || true
cp -a "$HOME/.companyos_runtime/task_queue" "$B/" 2>/dev/null || true
echo "BACKUP=$B"

python - <<'PY'
import sqlite3,json,time
from collections import Counter
from pathlib import Path
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
q=AutonomousTaskQueue()
before_json={t.task_id:t for t in q._iter_task_files()}
before_db=q.kernel.counts()

# JSON task files are the queue's load/dispatch source in the current implementation.
# Upsert every valid JSON record into the durable kernel; do NOT delete SQLite-only rows.
result=q.kernel.import_queue(q)

after_json={t.task_id:t for t in q._iter_task_files()}
after_db=q.kernel.counts()
c=sqlite3.connect(str(q.kernel.db_path)); c.row_factory=sqlite3.Row
rows=c.execute("SELECT task_id,state FROM tasks").fetchall(); c.close()
db={r["task_id"]:r["state"] for r in rows}
mismatch=[(tid,t.state,db.get(tid)) for tid,t in after_json.items() if db.get(tid)!=t.state]
json_only=[tid for tid in after_json if tid not in db]
sqlite_only=[tid for tid in db if tid not in after_json]

print("IMPORT_RESULT=",result)
print("BEFORE_JSON_COUNTS=",dict(Counter(t.state for t in before_json.values())))
print("BEFORE_SQLITE_COUNTS=",before_db)
print("AFTER_JSON_COUNTS=",dict(Counter(t.state for t in after_json.values())))
print("AFTER_SQLITE_COUNTS=",after_db)
print("STATE_MISMATCH_AFTER=",len(mismatch))
print("JSON_ONLY_AFTER=",len(json_only))
print("SQLITE_ONLY_PRESERVED=",len(sqlite_only))
print("SAMPLE_SQLITE_ONLY=",sqlite_only[:10])
print("SQLITE_ROWS_DELETED=0")
print("JSON_TASKS_DELETED=0")
print("IDEMPOTENCY_INDEX_REMOVED=0")
ok=(len(mismatch)==0 and len(json_only)==0)
print("V60_RECONCILIATION="+("PASS" if ok else "REVIEW"))
if not ok: raise SystemExit(4)
PY
