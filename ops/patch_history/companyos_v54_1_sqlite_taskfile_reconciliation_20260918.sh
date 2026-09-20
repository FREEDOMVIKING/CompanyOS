#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V54.1 READ-ONLY SQLITE/TASKFILE RECONCILIATION ====="

python - <<'PY'
import json, sqlite3, time
from pathlib import Path
from collections import Counter, defaultdict
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue

q=AutonomousTaskQueue()
tasks=list(q._iter_task_files())
file_by_id={t.task_id:t for t in tasks}
file_by_key=defaultdict(list)
for t in tasks:
    if t.idempotency_key:
        file_by_key[t.idempotency_key].append(t)

# Find current orphan planning chains exactly as V53 did.
orphans=[]
bygs=defaultdict(list)
for t in tasks:
    p=t.payload if isinstance(t.payload,dict) else {}
    if p.get("goal_id") and p.get("stage"):
        bygs[(str(p["goal_id"]),str(p["stage"]))].append(t)
for t in tasks:
    if t.state!="QUEUED": continue
    p=t.payload if isinstance(t.payload,dict) else {}
    if p.get("stage")=="planning" and p.get("depends_on_stage")=="research" and p.get("goal_id"):
        g=str(p["goal_id"])
        if not bygs.get((g,"research")):
            orphans.append((t,g,f"{g}:research"))

# Locate SQLite database from queue/kernel object first, then known runtime DBs.
candidates=[]
for obj in (q, getattr(q,"kernel",None)):
    if obj:
        for name in ("db_path","path","database_path"):
            v=getattr(obj,name,None)
            if v: candidates.append(Path(str(v)).expanduser())
candidates += [
    Path.home()/".companyos_runtime"/"tasks.sqlite3",
    Path.home()/".companyos_runtime"/"durable_execution.sqlite3",
]
db=None
for c in candidates:
    if c.exists():
        try:
            con=sqlite3.connect(str(c)); 
            if con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'").fetchone():
                db=c; con.close(); break
            con.close()
        except Exception: pass
if db is None:
    # bounded discovery fallback
    for c in (Path.home()/".companyos_runtime").glob("*.sqlite*"):
        try:
            con=sqlite3.connect(str(c))
            if con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'").fetchone():
                db=c; con.close(); break
            con.close()
        except Exception: pass
if db is None:
    raise SystemExit("V54_1_ABORT: tasks SQLite database not found")

con=sqlite3.connect(str(db)); con.row_factory=sqlite3.Row
cols=[r["name"] for r in con.execute("PRAGMA table_info(tasks)")]
wanted=["task_id","task_type","state","idempotency_key","payload_json","attempts","max_attempts",
        "last_error","created_at_unix","updated_at_unix","next_attempt_unix"]
select=[c for c in wanted if c in cols]
counts=Counter(); samples=defaultdict(list)
for planning,g,key in orphans:
    rows=con.execute(
        f"SELECT {','.join(select)} FROM tasks WHERE idempotency_key=?",(key,)
    ).fetchall()
    if not rows:
        cls="sqlite_key_missing"
    else:
        row=dict(rows[0]); tid=str(row.get("task_id",""))
        f=file_by_id.get(tid)
        if f is None:
            cls="sqlite_row_missing_taskfile"
        else:
            fp=f.payload if isinstance(f.payload,dict) else {}
            if fp.get("goal_id")!=g or fp.get("stage")!="research":
                cls="sqlite_and_file_metadata_mismatch"
            else:
                cls="research_present_but_v53_index_missed"
    counts[cls]+=1
    if len(samples[cls])<10:
        item={"goal_id":g,"expected_key":key,"planning_task_id":planning.task_id}
        if rows:
            item["sqlite_row"]={k:dict(rows[0]).get(k) for k in select}
            item["taskfile_visible_by_id"]=str(dict(rows[0]).get("task_id","")) in file_by_id
        samples[cls].append(item)

report={
 "mode":"READ_ONLY",
 "database":str(db),
 "tasks_columns":cols,
 "orphan_planning_examined":len(orphans),
 "reconciliation":dict(counts),
 "samples":dict(samples),
 "file_visible_states":dict(Counter(t.state for t in tasks)),
}
out=Path.home()/".companyos_runtime"/f"v54_1_sqlite_taskfile_reconciliation_{int(time.time())}.json"
out.write_text(json.dumps(report,indent=2,sort_keys=True,default=str)+"\n")
print(json.dumps(report,indent=2,sort_keys=True,default=str))
print("REPORT=",out)
print("DATABASE_WRITES=0")
print("QUEUE_RECORDS_CHANGED=0")
print("V54_1_RECONCILIATION=PASS")
con.close()
PY
