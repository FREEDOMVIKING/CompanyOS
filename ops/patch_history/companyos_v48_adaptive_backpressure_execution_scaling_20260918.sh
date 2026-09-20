#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
echo "===== COMPANYOS V48 ADAPTIVE BACKPRESSURE + EXECUTION SCALING ====="
STAMP="$(date +%Y%m%d_%H%M%S)"
R="$HOME/.companyos_runtime"; BACKUP="$R/backups/v48_$STAMP"
mkdir -p "$BACKUP"
cp -f companyos/runtime/execution_drain_engine.py "$BACKUP/" 2>/dev/null || true

cat > companyos/runtime/adaptive_backpressure.py <<'PY'
from __future__ import annotations
import json,time
from collections import Counter
from pathlib import Path
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue

class AdaptiveBackpressure:
    def __init__(self):
        self.queue=AutonomousTaskQueue()
        self.root=Path.home()/".companyos_runtime"
        self.state_path=self.root/"adaptive_backpressure_state.json"
    def snapshot(self):
        rows=list(self.queue._iter_task_files())
        q=Counter(t.task_type for t in rows if t.state=="QUEUED")
        return {"ts":time.time(),"queued":sum(q.values()),"queued_by_type":dict(q),
                "largest_type":max(q,key=q.get) if q else None}
    def previous(self):
        try:return json.loads(self.state_path.read_text())
        except:return {}
    def decide(self):
        cur=self.snapshot(); prev=self.previous()
        old=int(prev.get("snapshot",{}).get("queued",cur["queued"]))
        growth=cur["queued"]-old; backlog=cur["queued"]
        if backlog>=900 or growth>=20: divisor,batch=4,64
        elif backlog>=600 or growth>=8: divisor,batch=3,48
        elif backlog>=300 or growth>0: divisor,batch=2,40
        else: divisor,batch=1,24
        state={"timestamp_unix":time.time(),"snapshot":cur,"queue_growth":growth,
               "producer_divisor":divisor,"execution_batch":batch,
               "boost_type":cur["largest_type"]}
        tmp=self.state_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(state,indent=2,sort_keys=True)+"\n")
        tmp.replace(self.state_path)
        return state
PY

python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/execution_drain_engine.py")
if not p.exists(): raise SystemExit("V48_ABORT: execution_drain_engine.py missing")
s=p.read_text()
start=s.find("    def _rank(self, task: TaskRecord, unlocks: Counter) -> tuple:")
end=s.find("\n    def snapshot(",start)
if start<0 or end<0:
    if "boost_type: str | None" not in s: raise SystemExit("V48_ABORT: rank source changed")
else:
    new='''    def _rank(self, task: TaskRecord, unlocks: Counter, boost_type: str | None = None) -> tuple:
        payload = task.payload if isinstance(task.payload, dict) else {}
        gid = payload.get("goal_id")
        stage = payload.get("stage")
        downstream = unlocks.get((str(gid), str(stage)), 0) if gid and stage else 0
        boost = 0 if boost_type and task.task_type == boost_type else 1
        return (boost, float(task.created_at_unix), -downstream, -int(task.priority))
'''
    s=s[:start]+new+s[end:]
old='''        candidates = [t for t in before_tasks if self._ready(t, completed, now)]
        candidates.sort(key=lambda t: self._rank(t, unlocks))
        selected = candidates[:self.batch_size]
'''
new='''        candidates = [t for t in before_tasks if self._ready(t, completed, now)]
        queued_types = Counter(t.task_type for t in before_tasks if t.state == "QUEUED")
        boost_type = max(queued_types, key=queued_types.get) if queued_types else None
        candidates.sort(key=lambda t: self._rank(t, unlocks, boost_type))
        selected = candidates[:self.batch_size]
'''
if old in s:s=s.replace(old,new,1)
elif "queued_types = Counter" not in s: raise SystemExit("V48_ABORT: candidate source changed")
p.write_text(s)
PY

cat > scripts/companyos_v48ctl <<'PY'
#!/data/data/com.termux/files/usr/bin/python
import argparse,json,time
from companyos.runtime.adaptive_backpressure import AdaptiveBackpressure
from companyos.runtime.execution_drain_engine import ExecutionDrainEngine
p=argparse.ArgumentParser(); p.add_argument("cmd",choices=["status","cycle","run"])
p.add_argument("--cycles",type=int,default=6); p.add_argument("--sleep",type=float,default=10)
a=p.parse_args()
def cycle():
    d=AdaptiveBackpressure().decide()
    r=ExecutionDrainEngine(d["execution_batch"]).run_batch()
    return {"control":d,"drain":{"attempted":r["attempted"],"completed_delta":r["completed_delta"],
            "queue_delta":r["queue_delta"],"after":r["after"]}}
if a.cmd=="status": print(json.dumps(AdaptiveBackpressure().decide(),indent=2))
elif a.cmd=="cycle": print(json.dumps(cycle(),indent=2))
else:
    for i in range(max(1,min(a.cycles,60))):
        print(json.dumps({"cycle":i+1,**cycle()},indent=2),flush=True)
        if i+1<a.cycles: time.sleep(max(0,a.sleep))
PY
chmod +x scripts/companyos_v48ctl

python -m py_compile companyos/runtime/adaptive_backpressure.py companyos/runtime/execution_drain_engine.py scripts/companyos_v48ctl
echo "COMPILE=PASS"
python scripts/companyos_v48ctl status
echo "===== SAFE CONTROLLED LIVE CYCLE ====="
python scripts/companyos_v48ctl cycle
echo "SUPERVISOR_RESTART=NO"
echo "QUEUE_RECORDS_DELETED=0"
echo "FINANCE_CONNECTORS_CHANGED=0"
echo "V48_INSTALL=PASS"
echo "NEXT: cd ~/companyos && python scripts/companyos_v48ctl run --cycles 6 --sleep 10"
