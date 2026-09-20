#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.78 IDEMPOTENCY COLLISION FORENSICS ====="
echo "SOURCE_WRITES=0"
echo "QUEUE_WRITES=0"
echo "DB_WRITES=0"

python - <<'PY'
from pathlib import Path
import json, sqlite3
from collections import Counter, defaultdict

ROOT = Path.home() / "companyos"
RUNTIME = Path.home() / ".companyos_runtime"
QUEUE_DIR = RUNTIME / "task_queue"
DB = RUNTIME / "execution_kernel.sqlite3"

# ---------- JSON queue ----------
json_tasks = {}
json_by_key = defaultdict(list)
unreadable = []

for p in sorted(QUEUE_DIR.glob("*.json")):
    try:
        d = json.loads(p.read_text(errors="ignore"))
    except Exception as exc:
        unreadable.append((str(p), type(exc).__name__, str(exc)))
        continue

    tid = str(d.get("task_id") or p.stem)
    d["_path"] = str(p)
    json_tasks[tid] = d
    key = str(d.get("idempotency_key") or "")
    if key:
        json_by_key[key].append(d)

print("JSON_TASKS=", len(json_tasks))
print("JSON_UNREADABLE=", len(unreadable))
print("JSON_STATE_COUNTS=", dict(sorted(Counter(str(x.get("state") or "UNKNOWN") for x in json_tasks.values()).items())))

dup_json_keys = {k:v for k,v in json_by_key.items() if len(v) > 1}
print("JSON_DUPLICATE_IDEMPOTENCY_KEYS=", len(dup_json_keys))

# ---------- SQLite durable projection ----------
if not DB.exists():
    raise SystemExit("V65_78_ABORT=execution_kernel_db_missing")

con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
try:
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    rows = [dict(r) for r in con.execute(
        "SELECT task_id,idempotency_key,task_type,priority,state,assigned_agent,"
        "attempts,max_attempts,created_at_unix,updated_at_unix,next_attempt_unix,"
        "goal_id,stage,depends_on_stage,payload_json,result_json,last_error "
        "FROM tasks"
    ).fetchall()]
finally:
    con.close()

print("DB_INTEGRITY=", integrity)
print("DB_TASKS=", len(rows))
print("DB_STATE_COUNTS=", dict(sorted(Counter(str(x.get("state") or "UNKNOWN") for x in rows).items())))

db_by_id = {str(r["task_id"]): r for r in rows}
db_by_key = {}
for r in rows:
    key = str(r.get("idempotency_key") or "")
    if key:
        db_by_key[key] = r

# ---------- Cross-projection comparison ----------
exact_projection = 0
json_without_db_id = []
db_without_json_id = []
key_owner_conflicts = []
state_mismatches = []
safe_rebind_candidates = []
ambiguous_conflicts = []

for tid, jt in json_tasks.items():
    dr = db_by_id.get(tid)
    if dr:
        exact_projection += 1
        if str(jt.get("state")) != str(dr.get("state")):
            state_mismatches.append({
                "task_id": tid,
                "idempotency_key": jt.get("idempotency_key"),
                "json_state": jt.get("state"),
                "db_state": dr.get("state"),
                "json_attempts": jt.get("attempts"),
                "db_attempts": dr.get("attempts"),
                "json_updated": jt.get("updated_at_unix"),
                "db_updated": dr.get("updated_at_unix"),
                "json_last_error": jt.get("last_error"),
                "db_last_error": dr.get("last_error"),
            })
    else:
        json_without_db_id.append(jt)

    key = str(jt.get("idempotency_key") or "")
    if not key:
        continue

    owner = db_by_key.get(key)
    if owner and str(owner["task_id"]) != tid:
        payload = jt.get("payload") if isinstance(jt.get("payload"), dict) else {}
        try:
            db_payload = json.loads(owner.get("payload_json") or "{}")
        except Exception:
            db_payload = {}

        conflict = {
            "idempotency_key": key,
            "json_task_id": tid,
            "json_state": jt.get("state"),
            "json_attempts": jt.get("attempts"),
            "json_last_error": jt.get("last_error"),
            "json_goal_id": payload.get("goal_id"),
            "json_stage": payload.get("stage"),
            "json_depends_on_stage": payload.get("depends_on_stage"),
            "json_task_type": jt.get("task_type"),
            "json_updated_at": jt.get("updated_at_unix"),
            "db_owner_task_id": owner.get("task_id"),
            "db_owner_state": owner.get("state"),
            "db_owner_attempts": owner.get("attempts"),
            "db_owner_last_error": owner.get("last_error"),
            "db_owner_goal_id": owner.get("goal_id"),
            "db_owner_stage": owner.get("stage"),
            "db_owner_depends_on_stage": owner.get("depends_on_stage"),
            "db_owner_task_type": owner.get("task_type"),
            "db_owner_updated_at": owner.get("updated_at_unix"),
            "db_owner_has_json_file": str(owner.get("task_id")) in json_tasks,
            "same_goal": str(payload.get("goal_id")) == str(owner.get("goal_id")),
            "same_stage": str(payload.get("stage")) == str(owner.get("stage")),
            "same_task_type": str(jt.get("task_type")) == str(owner.get("task_type")),
        }

        key_owner_conflicts.append(conflict)

        if (
            not conflict["db_owner_has_json_file"]
            and conflict["same_goal"]
            and conflict["same_stage"]
            and conflict["same_task_type"]
        ):
            safe_rebind_candidates.append(conflict)
        else:
            ambiguous_conflicts.append(conflict)

for tid, dr in db_by_id.items():
    if tid not in json_tasks:
        db_without_json_id.append(dr)

print("EXACT_TASK_ID_PROJECTIONS=", exact_projection)
print("JSON_WITHOUT_DB_TASK_ID=", len(json_without_db_id))
print("DB_WITHOUT_JSON_TASK_ID=", len(db_without_json_id))
print("STATE_MISMATCHES_BY_TASK_ID=", len(state_mismatches))
print("IDEMPOTENCY_KEY_OWNER_CONFLICTS=", len(key_owner_conflicts))
print("SAFE_STALE_DB_OWNER_REBIND_CANDIDATES=", len(safe_rebind_candidates))
print("AMBIGUOUS_KEY_CONFLICTS=", len(ambiguous_conflicts))

if dup_json_keys:
    print("\n===== JSON DUPLICATE KEY SAMPLES =====")
    for key, group in list(dup_json_keys.items())[:20]:
        print("DUP_KEY=", key)
        for d in group:
            print(json.dumps({
                "task_id": d.get("task_id"),
                "state": d.get("state"),
                "task_type": d.get("task_type"),
                "attempts": d.get("attempts"),
                "goal_id": (d.get("payload") or {}).get("goal_id") if isinstance(d.get("payload"), dict) else None,
                "stage": (d.get("payload") or {}).get("stage") if isinstance(d.get("payload"), dict) else None,
                "last_error": d.get("last_error"),
                "updated_at_unix": d.get("updated_at_unix"),
            }, sort_keys=True, default=str))

if key_owner_conflicts:
    print("\n===== IDEMPOTENCY KEY OWNER CONFLICTS =====")
    for c in sorted(
        key_owner_conflicts,
        key=lambda x: float(x.get("json_updated_at") or 0),
        reverse=True
    )[:40]:
        print(json.dumps(c, sort_keys=True, default=str))

if state_mismatches:
    print("\n===== TASK-ID STATE MISMATCHES =====")
    for x in sorted(
        state_mismatches,
        key=lambda y: float(y.get("json_updated") or 0),
        reverse=True
    )[:30]:
        print(json.dumps(x, sort_keys=True, default=str))

if json_without_db_id:
    print("\n===== JSON TASKS WITHOUT SAME TASK_ID IN DB =====")
    for d in sorted(
        json_without_db_id,
        key=lambda x: float(x.get("updated_at_unix") or 0),
        reverse=True
    )[:30]:
        payload = d.get("payload") if isinstance(d.get("payload"), dict) else {}
        key = str(d.get("idempotency_key") or "")
        owner = db_by_key.get(key)
        print(json.dumps({
            "task_id": d.get("task_id"),
            "idempotency_key": key,
            "state": d.get("state"),
            "attempts": d.get("attempts"),
            "task_type": d.get("task_type"),
            "goal_id": payload.get("goal_id"),
            "stage": payload.get("stage"),
            "depends_on_stage": payload.get("depends_on_stage"),
            "last_error": d.get("last_error"),
            "updated_at_unix": d.get("updated_at_unix"),
            "db_key_owner_task_id": owner.get("task_id") if owner else None,
            "db_key_owner_state": owner.get("state") if owner else None,
        }, sort_keys=True, default=str))

print("\n===== SUMMARY =====")
print("COLLISION_ROOT_PRESENT=", bool(key_owner_conflicts))
print("ALL_KEY_CONFLICTS_SAFE_STALE_OWNER=", bool(key_owner_conflicts) and not ambiguous_conflicts and len(safe_rebind_candidates) == len(key_owner_conflicts))

if key_owner_conflicts and not ambiguous_conflicts:
    print("REPAIR_CLASS=STALE_DB_IDEMPOTENCY_OWNER_REBIND")
elif key_owner_conflicts:
    print("REPAIR_CLASS=MIXED_OR_AMBIGUOUS_REQUIRES_TARGETED_RECONCILIATION")
elif state_mismatches:
    print("REPAIR_CLASS=STATE_PROJECTION_RECONCILIATION")
else:
    print("REPAIR_CLASS=NO_IDEMPOTENCY_COLLISION_FOUND")

print("V65_78_IDEMPOTENCY_COLLISION_FORENSICS=COMPLETE")
PY
