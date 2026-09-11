from __future__ import annotations
import json, time, uuid
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class ArtifactRecord:
    artifact_id: str
    project_id: str
    name: str
    artifact_type: str
    location: str
    state: str
    created_at_unix: float
    metadata: dict

class ArtifactRegistry:
    def __init__(self, root=None):
        self.root=root or (Path.home()/".companyos_runtime"/"artifacts")
        self.root.mkdir(parents=True,exist_ok=True)

    def add(self, project_id, name, artifact_type, location, state="INTERNAL", metadata=None):
        r=ArtifactRecord(str(uuid.uuid4()),project_id,name,artifact_type,location,state,time.time(),dict(metadata or {}))
        (self.root/f"{r.artifact_id}.json").write_text(json.dumps(asdict(r),indent=2,sort_keys=True)+"\n")
        return r
