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
