from __future__ import annotations
import json, time, uuid
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class ExperimentRecord:
    experiment_id: str
    project_id: str
    hypothesis: str
    state: str
    success_metric: str
    baseline: float
    target: float
    created_at_unix: float
    updated_at_unix: float
    result_value: float | None
    metadata: dict

class ExperimentManager:
    def __init__(self, root=None):
        self.root=root or (Path.home()/".companyos_runtime"/"experiments")
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self, project_id, hypothesis, success_metric, baseline, target, metadata=None):
        now=time.time()
        r=ExperimentRecord(str(uuid.uuid4()),project_id,hypothesis,"PLANNED",success_metric,float(baseline),float(target),now,now,None,dict(metadata or {}))
        self.save(r); return r

    def save(self,r):
        (self.root/f"{r.experiment_id}.json").write_text(json.dumps(asdict(r),indent=2,sort_keys=True)+"\n")

    def complete(self,experiment_id,result_value):
        r=ExperimentRecord(**json.loads((self.root/f"{experiment_id}.json").read_text()))
        r.result_value=float(result_value)
        r.state="SUCCESS" if r.result_value >= r.target else "FAILED"
        r.updated_at_unix=time.time()
        self.save(r); return r
