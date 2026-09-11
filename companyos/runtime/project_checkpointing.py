from __future__ import annotations
import json, time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

@dataclass
class ProjectCheckpoint:
    project_id: str
    stage: str
    timestamp_unix: float
    snapshot: dict[str, Any]

class ProjectCheckpointStore:
    def __init__(self, root=None):
        self.root = root or (Path.home()/".companyos_runtime"/"project_checkpoints")
        self.root.mkdir(parents=True, exist_ok=True)

    def write(self, project_id, stage, snapshot):
        cp = ProjectCheckpoint(project_id, stage, time.time(), dict(snapshot))
        p = self.root/f"{project_id}_{int(cp.timestamp_unix*1000)}.json"
        p.write_text(json.dumps(asdict(cp), indent=2, sort_keys=True)+"\n")
        return cp
