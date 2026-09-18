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
