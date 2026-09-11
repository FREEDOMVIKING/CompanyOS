from __future__ import annotations
import json, time, uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

@dataclass
class ApprovalItem:
    approval_id: str
    title: str
    action_type: str
    reason: str
    payload: dict[str, Any]
    state: str
    created_at_unix: float
    updated_at_unix: float

class ApprovalQueue:
    def __init__(self, root=None):
        self.root = root or (Path.home()/".companyos_runtime"/"approval_queue")
        self.root.mkdir(parents=True, exist_ok=True)

    def add(self, title, action_type, reason, payload=None):
        now = time.time()
        item = ApprovalItem(str(uuid.uuid4()), title, action_type, reason,
                            dict(payload or {}), "PENDING", now, now)
        self.save(item)
        return item

    def save(self,item):
        p=self.root/f"{item.approval_id}.json"
        t=p.with_suffix(".json.tmp")
        t.write_text(json.dumps(asdict(item),indent=2,sort_keys=True)+"\n")
        t.replace(p)

    def all(self):
        out=[]
        for p in self.root.glob("*.json"):
            try: out.append(ApprovalItem(**json.loads(p.read_text())))
            except Exception: pass
        return out
