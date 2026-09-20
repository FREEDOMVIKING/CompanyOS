#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"; export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V61 FINISH HISTORICAL RECOVERY ====="
V57="$HOME/storage/downloads/companyos_v57_authoritative_recovery_drain_20260918.sh"
[ -f "$V57" ] || { echo "V61_ABORT=V57 missing: $V57"; exit 2; }
MAX="${COMPANYOS_V61_MAX_BATCHES:-20}"
for i in $(seq 1 "$MAX"); do
  echo "===== V61 BATCH $i/$MAX ====="
  COMPANYOS_V57_RESTORE_LIMIT=16 bash "$V57"
  R="$(ls -1t "$HOME"/.companyos_runtime/v57_authoritative_recovery_*.json 2>/dev/null | head -1 || true)"
  [ -n "$R" ] || { echo "V61_ABORT=no V57 report"; exit 3; }
  read -r ELIG REST BAD <<<"$(python - "$R" <<'PY'
import json,sys
r=json.load(open(sys.argv[1]))
s=r.get("restored_states",{})
bad=sum(v not in ("COMPLETED","QUEUED") for v in s.values())
print(int(r.get("eligible_historical_missing_research",0)),int(r.get("restored_count",0)),bad)
PY
)"
  echo "V61_STATUS eligible=$ELIG restored=$REST unexpected_states=$BAD"
  [ "$BAD" -ne 0 ] && { echo "V61_ABORT=unexpected restored task state"; exit 4; }
  [ "$ELIG" -eq 0 ] && break
  [ "$REST" -eq 0 ] && { echo "V61_ABORT=eligible tasks found but none restored"; exit 5; }
done

python - <<'PY'
import sqlite3
from collections import Counter
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
q=AutonomousTaskQueue()
jc=Counter(t.state for t in q._iter_task_files())
c=sqlite3.connect(str(q.kernel.db_path)); c.row_factory=sqlite3.Row
rows=c.execute("SELECT state,count(*) n FROM tasks GROUP BY state").fetchall()
failed_missing=c.execute("""SELECT count(*) n FROM tasks t WHERE state='FAILED'
 AND task_type='research' AND stage='research'
 AND last_error LIKE '%NameError%result%'""").fetchone()["n"]
c.close()
print("FINAL_JSON_COUNTS=",dict(jc))
print("FINAL_SQLITE_COUNTS=",{r["state"]:r["n"] for r in rows})
print("REMAINING_LEGACY_RESULT_FAILURES=",failed_missing)
print("V61_HISTORICAL_RECOVERY=PASS")
PY
