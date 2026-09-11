from __future__ import annotations
import json, time, uuid
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class SalesLead:
    lead_id: str
    project_id: str
    source: str
    stage: str
    value_estimate: float
    created_at_unix: float
    metadata: dict

class SalesPipeline:
    def __init__(self, root=None):
        self.root=root or (Path.home()/".companyos_runtime"/"sales_pipeline")
        self.root.mkdir(parents=True,exist_ok=True)

    def add(self,project_id,source,value_estimate=0,metadata=None):
        r=SalesLead(str(uuid.uuid4()),project_id,source,"NEW",float(value_estimate),time.time(),dict(metadata or {}))
        (self.root/f"{r.lead_id}.json").write_text(json.dumps(asdict(r),indent=2,sort_keys=True)+"\n")
        return r
