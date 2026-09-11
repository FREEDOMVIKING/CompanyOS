from __future__ import annotations
import json, time
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class KPIRecord:
    kpi_id: str
    name: str
    value: float
    unit: str
    updated_at_unix: float
    metadata: dict

class KPIRegistry:
    def __init__(self, root=None):
        self.root = root or (Path.home()/".companyos_runtime"/"kpis")
        self.root.mkdir(parents=True, exist_ok=True)

    def upsert(self, kpi_id, name, value, unit="", metadata=None):
        rec = KPIRecord(str(kpi_id), str(name), float(value), str(unit), time.time(), dict(metadata or {}))
        (self.root/f"{rec.kpi_id}.json").write_text(json.dumps(asdict(rec), indent=2, sort_keys=True)+"\n")
        return rec

    def all(self):
        out=[]
        for p in self.root.glob("*.json"):
            try: out.append(KPIRecord(**json.loads(p.read_text())))
            except Exception: pass
        return out
