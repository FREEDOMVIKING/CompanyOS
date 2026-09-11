from __future__ import annotations
import json, time, uuid
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class ReleaseCandidate:
    release_id: str
    project_id: str
    version: str
    state: str
    created_at_unix: float
    notes: str

class ReleaseCandidateManager:
    def __init__(self, root=None):
        self.root=root or (Path.home()/".companyos_runtime"/"release_candidates")
        self.root.mkdir(parents=True,exist_ok=True)

    def create(self, project_id, version, notes=""):
        r=ReleaseCandidate(str(uuid.uuid4()),project_id,version,"INTERNAL_RC",time.time(),notes)
        (self.root/f"{r.release_id}.json").write_text(json.dumps(asdict(r),indent=2,sort_keys=True)+"\n")
        return r
