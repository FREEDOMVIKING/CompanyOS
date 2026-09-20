#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACK="$HOME/.companyos_runtime/backups/v28_$STAMP"
mkdir -p "$BACK/companyos/runtime"
for f in autonomous_task_queue.py autonomous_task_dispatcher.py dependency_aware_dispatcher.py; do cp -a "companyos/runtime/$f" "$BACK/companyos/runtime/$f"; done
restore(){ echo "V28_FAIL - restoring"; cp -a "$BACK/companyos/runtime/." companyos/runtime/; }
trap restore ERR

python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/autonomous_task_queue.py"); s=p.read_text()
a=s.index("    def bounded_candidates_window("); b=s.index("    def bounded_candidates(",a)
new="""    def bounded_candidates_window(self, limit: int = 1000, offset: int = 0) -> list[TaskRecord]:
        limit=max(1,int(limit)); offset=max(0,int(offset))
        files=sorted(self.root.glob("*.json"),key=lambda p:p.name)
        if not files: return []
        start=offset % len(files)
        ordered=files[start:]+files[:start]
        tasks=[]
        for path in ordered[:limit]:
            try: tasks.append(TaskRecord(**json.loads(path.read_text(encoding="utf-8"))))
            except Exception: continue
        return tasks

"""
s=s[:a]+new+s[b:]
s=s.replace("candidates.sort(key=lambda t: (t.priority, t.created_at_unix))","candidates.sort(key=lambda t: (-int(t.priority), float(t.created_at_unix)))")
p.write_text(s)
PY

cat > companyos/runtime/autonomous_task_dispatcher.py <<'PY'
from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Any,Callable,Optional
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue,TaskRecord
@dataclass(frozen=True)
class DispatchResult:
    dispatched:bool; task_id:Optional[str]; agent_name:Optional[str]; state:Optional[str]; reason:str; result:Any
class AutonomousTaskDispatcher:
    def __init__(self,queue:AutonomousTaskQueue|None=None)->None:
        self.queue=queue or AutonomousTaskQueue(); self.handlers={}
    def register(self,*,task_type:str,agent_name:str,handler:Callable[[TaskRecord],Any])->None:
        self.handlers[task_type]=(agent_name,handler)
    def dispatch_task(self,task:TaskRecord)->DispatchResult:
        now=time.time(); task=self.queue.load(task.task_id)
        if task.state!="QUEUED": return DispatchResult(False,task.task_id,None,task.state,"task_not_queued",None)
        if task.attempts>=task.max_attempts: return DispatchResult(False,task.task_id,None,task.state,"attempts_exhausted",None)
        if task.next_attempt_unix>now: return DispatchResult(False,task.task_id,None,task.state,"retry_not_due",None)
        if task.task_type not in self.handlers: return DispatchResult(False,task.task_id,None,task.state,"unsupported_task_type",None)
        agent,handler=self.handlers[task.task_type]
        task.state="CLAIMED"; task.assigned_agent=agent; task.updated_at_unix=now; self.queue.save(task); self.queue.mark_running(task)
        try:
            result=handler(task); self.queue.complete(task,result)
            return DispatchResult(True,task.task_id,agent,task.state,"completed",result)
        except Exception as exc:
            self.queue.fail(task,f"{type(exc).__name__}:{exc}",retry_delay_seconds=30)
            return DispatchResult(True,task.task_id,agent,task.state,"handler_failed",None)
    def dispatch_next(self)->DispatchResult:
        now=time.time()
        c=[t for t in self.queue.bounded_candidates(1024) if t.task_type in self.handlers and t.next_attempt_unix<=now]
        if not c:return DispatchResult(False,None,None,None,"no_supported_task_available",None)
        c.sort(key=lambda t:(-int(t.priority),float(t.created_at_unix),t.task_id))
        return self.dispatch_task(c[0])
PY

cat > companyos/runtime/dependency_aware_dispatcher.py <<'PY'
from __future__ import annotations
import os,time
from companyos.runtime.autonomous_task_dispatcher import AutonomousTaskDispatcher,DispatchResult
class DependencyAwareDispatcher:
    def __init__(self,dispatcher:AutonomousTaskDispatcher)->None:self.dispatcher=dispatcher;self.queue=dispatcher.queue
    def _dependency_satisfied(self,task)->bool:
        p=task.payload if isinstance(task.payload,dict) else {}; dep=p.get("depends_on_stage")
        return True if not dep else self.queue.has_completed_goal_stage(p.get("goal_id"),dep)
    def dispatch_next(self)->DispatchResult:
        limit=max(1,int(os.getenv("COMPANYOS_QUEUE_SCAN_LIMIT","1000"))); cp=self.queue.root.parent/"dispatcher_scan_cursor.txt"
        try:cursor=int(cp.read_text().strip()) if cp.exists() else 0
        except Exception:cursor=0
        source=self.queue.bounded_candidates_window(limit,cursor); total=sum(1 for _ in self.queue.root.glob("*.json"))
        try:cp.write_text(str((cursor+limit)%max(1,total)))
        except Exception:pass
        now=time.time()
        c=[t for t in source if t.state=="QUEUED" and t.attempts<t.max_attempts and t.next_attempt_unix<=now and t.task_type in self.dispatcher.handlers and self._dependency_satisfied(t)]
        if not c:return DispatchResult(False,None,None,None,"no_dependency_ready_task",None)
        c.sort(key=lambda t:(-int(t.priority),float(t.created_at_unix),t.task_id))
        return self.dispatcher.dispatch_task(c[0])
PY

python -m py_compile companyos/runtime/autonomous_task_queue.py companyos/runtime/autonomous_task_dispatcher.py companyos/runtime/dependency_aware_dispatcher.py
python - <<'PY'
import tempfile,time
from pathlib import Path
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.autonomous_task_dispatcher import AutonomousTaskDispatcher
from companyos.runtime.dependency_aware_dispatcher import DependencyAwareDispatcher
with tempfile.TemporaryDirectory() as d:
 q=AutonomousTaskQueue(Path(d));x=AutonomousTaskDispatcher(q);x.register(task_type="research",agent_name="r",handler=lambda t:"ok")
 lo=q.enqueue(task_type="research",payload={},priority=10,idempotency_key="lo");hi=q.enqueue(task_type="research",payload={},priority=100,idempotency_key="hi")
 assert x.dispatch_next().task_id==hi.task_id
 delayed=q.enqueue(task_type="research",payload={},priority=999,idempotency_key="delay");delayed.next_attempt_unix=time.time()+3600;q.save(delayed)
 assert x.dispatch_next().task_id==lo.task_id
with tempfile.TemporaryDirectory() as d:
 q=AutonomousTaskQueue(Path(d));x=AutonomousTaskDispatcher(q)
 x.register(task_type="research",agent_name="r",handler=lambda t:"r");x.register(task_type="planning",agent_name="p",handler=lambda t:"p")
 p=q.enqueue(task_type="planning",payload={"goal_id":"g","depends_on_stage":"research"},priority=999,idempotency_key="p")
 r=q.enqueue(task_type="research",payload={"goal_id":"g","stage":"research"},priority=1,idempotency_key="r")
 y=DependencyAwareDispatcher(x);assert y.dispatch_next().task_id==r.task_id;assert y.dispatch_next().task_id==p.task_id
print("V28_REGRESSION_PASS")
PY
echo "V28_SOLID_FIX_PASS"
echo "BACKUP=$BACK"
echo "QUEUE_RECORDS_DELETED=0"
echo "SUPERVISOR_RESTARTED=NO"
trap - ERR
