#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  status)
    python - <<'PY'
import json
from companyos.workerops import WorkerOpsStatus
print(json.dumps(WorkerOpsStatus().status(),indent=2))
PY
    ;;
  verify)
    python "$ROOT/scripts/phase15501_16000_verify.py"
    ;;
  drain)
    python - <<'PY'
from pathlib import Path
import json
from companyos.daemonops import DurableJobQueue
from companyos.workerops import DurableWorkerPool
root=Path.home()/"companyos"
q=DurableJobQueue(root)
pool=DurableWorkerPool(root)
results=[]
for i in range(100):
    r=pool.process_one(q,worker_id="drain_worker",tick=i+1)
    results.append(r)
    if not r.get("processed"):
        break
print(json.dumps({"success":True,"processed":sum(1 for x in results if x.get("processed")),"remaining":len([j for j in q.load() if j.get("status") in ("queued","retry","running")]),"results":results[-10:]},indent=2,default=str))
PY
    ;;
  *)
    echo "Usage: $0 {status|verify|drain}"
    exit 2
    ;;
esac
