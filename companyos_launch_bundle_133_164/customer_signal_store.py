from __future__ import annotations
import json, time, uuid
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class CustomerSignal:
    signal_id: str
    project_id: str
    source: str
    sentiment: str
    text: str
    created_at_unix: float
    metadata: dict

class CustomerSignalStore:
    def __init__(self, root=None):
        self.root=root or (Path.home()/".companyos_runtime"/"customer_signals")
        self.root.mkdir(parents=True,exist_ok=True)

    def add(self,project_id,source,sentiment,text,metadata=None):
        r=CustomerSignal(str(uuid.uuid4()),project_id,source,sentiment,text,time.time(),dict(metadata or {}))
        (self.root/f"{r.signal_id}.json").write_text(json.dumps(asdict(r),indent=2,sort_keys=True)+"\n")
        return r
