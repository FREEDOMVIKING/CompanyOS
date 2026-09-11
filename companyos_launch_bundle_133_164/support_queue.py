from __future__ import annotations
import json, time, uuid
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class SupportItem:
    support_id: str
    project_id: str
    summary: str
    priority: int
    state: str
    created_at_unix: float

class SupportQueue:
    def __init__(self, root=None):
        self.root=root or (Path.home()/".companyos_runtime"/"support_queue")
        self.root.mkdir(parents=True,exist_ok=True)

    def add(self,project_id,summary,priority=100):
        r=SupportItem(str(uuid.uuid4()),project_id,summary,int(priority),"OPEN",time.time())
        (self.root/f"{r.support_id}.json").write_text(json.dumps(asdict(r),indent=2,sort_keys=True)+"\n")
        return r
