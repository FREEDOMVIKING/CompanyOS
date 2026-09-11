from __future__ import annotations
import json, time, uuid
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class RiskRecord:
    risk_id: str
    project_id: str
    description: str
    probability: float
    impact: float
    score: float
    mitigation: str
    state: str
    updated_at_unix: float

class RiskRegister:
    def __init__(self, root=None):
        self.root=root or (Path.home()/".companyos_runtime"/"risks")
        self.root.mkdir(parents=True,exist_ok=True)

    def add(self, project_id, description, probability, impact, mitigation=""):
        p=max(0,min(1,float(probability))); i=max(0,min(1,float(impact)))
        r=RiskRecord(str(uuid.uuid4()),project_id,description,p,i,round(p*i*100,2),mitigation,"OPEN",time.time())
        (self.root/f"{r.risk_id}.json").write_text(json.dumps(asdict(r),indent=2,sort_keys=True)+"\n")
        return r
