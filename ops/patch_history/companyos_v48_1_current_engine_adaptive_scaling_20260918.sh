#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
echo "===== COMPANYOS V48.1 CURRENT-ENGINE ADAPTIVE SCALING ====="
STAMP="$(date +%Y%m%d_%H%M%S)"; R="$HOME/.companyos_runtime"; B="$R/backups/v48_1_$STAMP"; mkdir -p "$B"
cp -f companyos/runtime/adaptive_backpressure.py "$B/" 2>/dev/null || true
cp -f companyos/runtime/dependency_aware_dispatcher.py "$B/" 2>/dev/null || true
cp -f companyos/runtime/autonomous_ceo_orchestrator.py "$B/" 2>/dev/null || true

cat > companyos/runtime/adaptive_backpressure.py <<'PY'
from __future__ import annotations
import json,time
from collections import Counter
from pathlib import Path
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
class AdaptiveBackpressure:
    def __init__(self,queue=None):
        self.queue=queue or AutonomousTaskQueue()
        self.state_path=Path.home()/".companyos_runtime"/"adaptive_backpressure_state.json"
    def decide(self):
        rows=list(self.queue._iter_task_files()); q=Counter(t.task_type for t in rows if t.state=="QUEUED")
        cur={"queued":sum(q.values()),"queued_by_type":dict(q),"largest_type":max(q,key=q.get) if q else None}
        try: prev=json.loads(self.state_path.read_text())
        except: prev={}
        growth=cur["queued"]-int(prev.get("snapshot",{}).get("queued",cur["queued"])); n=cur["queued"]
        if n>=900 or growth>=20: divisor,batch=4,64
        elif n>=600 or growth>=8: divisor,batch=3,48
        elif n>=300 or growth>0: divisor,batch=2,32
        else: divisor,batch=1,16
        out={"timestamp_unix":time.time(),"snapshot":cur,"queue_growth":growth,"producer_divisor":divisor,
             "execution_batch":batch,"boost_type":cur["largest_type"]}
        self.state_path.parent.mkdir(parents=True,exist_ok=True)
        self.state_path.write_text(json.dumps(out,indent=2)+"\n")
        return out
PY

python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/dependency_aware_dispatcher.py"); s=p.read_text()
old='''        candidates.sort(
            key=lambda t: (-int(t.priority), float(t.created_at_unix), t.task_id)
        )
'''
new='''        try:
            from companyos.runtime.adaptive_backpressure import AdaptiveBackpressure
            boost_type = AdaptiveBackpressure(self.queue).decide().get("boost_type")
        except Exception:
            boost_type = None
        candidates.sort(key=lambda t: (
            0 if boost_type and t.task_type == boost_type else 1,
            float(t.created_at_unix), -int(t.priority), t.task_id))
'''
if old in s: s=s.replace(old,new,1)
elif "boost_type = AdaptiveBackpressure" not in s: raise SystemExit("V48_1_ABORT: dispatcher source mismatch")
p.write_text(s)
PY

python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/autonomous_ceo_orchestrator.py"); s=p.read_text()
old='''        import os
        batch_size = max(1, min(int(os.getenv("COMPANYOS_TASKS_PER_CEO_CYCLE", "8")), 64))
        batch = self.execution_loop.run_bounded_batch(max_dispatches=batch_size)
'''
new='''        import os
        try:
            from companyos.runtime.adaptive_backpressure import AdaptiveBackpressure
            adaptive_batch = int(AdaptiveBackpressure(self.queue).decide().get("execution_batch", 8))
        except Exception:
            adaptive_batch = int(os.getenv("COMPANYOS_TASKS_PER_CEO_CYCLE", "8"))
        batch_size = max(1, min(adaptive_batch, 64))
        batch = self.execution_loop.run_bounded_batch(max_dispatches=batch_size)
'''
if old in s: s=s.replace(old,new,1)
elif "adaptive_batch = int(AdaptiveBackpressure" not in s: raise SystemExit("V48_1_ABORT: orchestrator source mismatch")
p.write_text(s)
PY

cat > scripts/companyos_v48ctl <<'PY'
#!/data/data/com.termux/files/usr/bin/python
import json
from companyos.runtime.adaptive_backpressure import AdaptiveBackpressure
print(json.dumps(AdaptiveBackpressure().decide(),indent=2))
PY
chmod +x scripts/companyos_v48ctl
python -m py_compile companyos/runtime/adaptive_backpressure.py companyos/runtime/dependency_aware_dispatcher.py companyos/runtime/autonomous_ceo_orchestrator.py scripts/companyos_v48ctl
echo "COMPILE=PASS"
python scripts/companyos_v48ctl
python - <<'PY'
from companyos.runtime.autonomous_goal_execution_loop import AutonomousGoalExecutionLoop
loop=AutonomousGoalExecutionLoop()
print("LIVE_LOOP=PASS")
print("HANDLERS=",sorted(loop.dispatcher.dispatcher.handlers))
PY
git add companyos/runtime/adaptive_backpressure.py companyos/runtime/dependency_aware_dispatcher.py companyos/runtime/autonomous_ceo_orchestrator.py scripts/companyos_v48ctl
git commit -m "V48.1 adaptive queue backpressure and execution scaling" || true
git push origin "$(git branch --show-current)"
echo "SUPERVISOR_RESTARTED=NO"
echo "QUEUE_RECORDS_DELETED=0"
echo "FINANCE_CONNECTORS_CHANGED=0"
echo "V48_1_INSTALL=PASS"
echo "NEXT=rerun_V47_profiler"
