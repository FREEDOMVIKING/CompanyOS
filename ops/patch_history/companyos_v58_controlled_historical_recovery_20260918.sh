#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"; export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V58 CONTROLLED HISTORICAL RECOVERY ====="
export COMPANYOS_V57_RESTORE_LIMIT="${COMPANYOS_V57_RESTORE_LIMIT:-16}"
MAX_BATCHES="${COMPANYOS_V58_MAX_BATCHES:-8}"
SCRIPT="${COMPANYOS_V57_SCRIPT:-$HOME/storage/downloads/companyos_v57_authoritative_recovery_drain_20260918.sh}"
[ -f "$SCRIPT" ] || { echo "V58_ABORT=V57 script not found: $SCRIPT"; exit 2; }

for i in $(seq 1 "$MAX_BATCHES"); do
  echo "===== V58 BATCH $i/$MAX_BATCHES ====="
  bash "$SCRIPT"
  latest="$(ls -1t "$HOME"/.companyos_runtime/v57_authoritative_recovery_*.json 2>/dev/null | head -1 || true)"
  [ -n "$latest" ] || { echo "V58_ABORT=no V57 report"; exit 3; }
  decision="$(python - "$latest" <<'PY'
import json,sys
r=json.load(open(sys.argv[1]))
rest=int(r.get("restored_count",0))
eligible=int(r.get("eligible_historical_missing_research",0))
states=r.get("restored_states",{})
bad=[k for k,v in states.items() if v not in ("COMPLETED","QUEUED")]
print("ABORT" if bad else ("DONE" if rest==0 or eligible==0 else "CONTINUE"))
PY
)"
  echo "V58_DECISION=$decision"
  [ "$decision" = "ABORT" ] && { echo "V58_RECOVERY=ABORTED_ON_UNEXPECTED_STATE"; exit 4; }
  [ "$decision" = "DONE" ] && break
done

python - <<'PY'
from collections import Counter
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
q=AutonomousTaskQueue()
print("FINAL_QUEUE_COUNTS="+str(dict(Counter(t.state for t in q._iter_task_files()))))
print("FINAL_SQLITE_COUNTS="+str(q.kernel.counts()))
print("V58_CONTROLLED_RECOVERY=PASS")
PY
