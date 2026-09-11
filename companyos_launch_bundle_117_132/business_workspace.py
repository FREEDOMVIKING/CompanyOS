from __future__ import annotations
import json, time
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class BusinessWorkspace:
    business_id: str
    name: str
    state: str
    active_projects: list[str]
    created_at_unix: float
    updated_at_unix: float

class BusinessWorkspaceStore:
    def __init__(self, root=None):
        self.root=root or (Path.home()/".companyos_runtime"/"businesses")
        self.root.mkdir(parents=True,exist_ok=True)

    def create(self,business_id,name):
        now=time.time()
        b=BusinessWorkspace(business_id,name,"ACTIVE",[],now,now)
        self.save(b); return b

    def save(self,b):
        p=self.root/f"{b.business_id}.json"
        p.write_text(json.dumps(asdict(b),indent=2,sort_keys=True)+"\n")

    def load(self,business_id):
        return BusinessWorkspace(**json.loads((self.root/f"{business_id}.json").read_text()))
