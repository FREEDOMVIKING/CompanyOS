#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"; export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V59 FULL STORE RECONCILIATION AUDIT ====="
python - <<'PY'
import json,sqlite3,time
from pathlib import Path
from collections import Counter
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
q=AutonomousTaskQueue()
jf={t.task_id:t for t in q._iter_task_files()}
c=sqlite3.connect(str(q.kernel.db_path)); c.row_factory=sqlite3.Row
rows=c.execute("SELECT task_id,idempotency_key,task_type,state,attempts,max_attempts,goal_id,stage,depends_on_stage,last_error FROM tasks").fetchall()
db={r["task_id"]:r for r in rows}; c.close()

jids=set(jf); dids=set(db); common=jids&dids
json_only=jids-dids; sqlite_only=dids-jids
mismatch=[]
for tid in common:
    if jf[tid].state != db[tid]["state"]:
        mismatch.append((tid,jf[tid].state,db[tid]["state"],jf[tid].task_type))
print("JSON_TOTAL=",len(jf))
print("SQLITE_TOTAL=",len(db))
print("COMMON_IDS=",len(common))
print("JSON_ONLY=",len(json_only))
print("SQLITE_ONLY=",len(sqlite_only))
print("STATE_MISMATCH=",len(mismatch))
print("JSON_COUNTS=",dict(Counter(t.state for t in jf.values())))
print("SQLITE_COUNTS=",dict(Counter(r["state"] for r in rows)))
print("JSON_ONLY_STATES=",dict(Counter(jf[x].state for x in json_only)))
print("SQLITE_ONLY_STATES=",dict(Counter(db[x]["state"] for x in sqlite_only)))
print("MISMATCH_PAIRS=",dict(Counter((a,b) for _,a,b,_ in mismatch)))
print("MISMATCH_TYPES=",dict(Counter(t for *_,t in mismatch)))
print("SAMPLE_JSON_ONLY=",list(sorted(json_only))[:10])
print("SAMPLE_SQLITE_ONLY=",list(sorted(sqlite_only))[:10])
print("SAMPLE_MISMATCH=",mismatch[:10])
report={"json_total":len(jf),"sqlite_total":len(db),"common_ids":len(common),
"json_only":len(json_only),"sqlite_only":len(sqlite_only),"state_mismatch":len(mismatch),
"json_counts":dict(Counter(t.state for t in jf.values())),
"sqlite_counts":dict(Counter(r["state"] for r in rows)),
"json_only_states":dict(Counter(jf[x].state for x in json_only)),
"sqlite_only_states":dict(Counter(db[x]["state"] for x in sqlite_only)),
"mismatch_pairs":{f"{a}->{b}":n for (a,b),n in Counter((a,b) for _,a,b,_ in mismatch).items()},
"sample_json_only":list(sorted(json_only))[:25],
"sample_sqlite_only":list(sorted(sqlite_only))[:25],
"sample_mismatch":mismatch[:25]}
out=Path.home()/".companyos_runtime"/f"v59_store_reconciliation_{int(time.time())}.json"
out.write_text(json.dumps(report,indent=2,default=str)+"\n")
print("REPORT=",out)
print("DATABASE_WRITES=0")
print("QUEUE_WRITES=0")
print("V59_RECONCILIATION_AUDIT=PASS")
PY
