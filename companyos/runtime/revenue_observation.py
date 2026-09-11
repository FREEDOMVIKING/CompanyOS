from __future__ import annotations
import json, time
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class RevenueObservation:
    observation_id: str
    project_id: str
    source: str
    amount: float
    currency: str
    timestamp_unix: float
    metadata: dict

class RevenueObservationStore:
    def __init__(self, root=None):
        self.root=root or (Path.home()/".companyos_runtime"/"revenue_observations")
        self.root.mkdir(parents=True,exist_ok=True)

    def add(self, observation_id, project_id, source, amount, currency="USD", metadata=None):
        rec=RevenueObservation(observation_id,project_id,source,float(amount),currency,time.time(),dict(metadata or {}))
        (self.root/f"{observation_id}.json").write_text(json.dumps(asdict(rec),indent=2,sort_keys=True)+"\n")
        return rec
