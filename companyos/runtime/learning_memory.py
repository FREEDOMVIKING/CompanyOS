from __future__ import annotations
import json, time, uuid
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class LearningRecord:
    learning_id: str
    source_type: str
    source_id: str
    lesson: str
    confidence: float
    created_at_unix: float
    metadata: dict

class LearningMemory:
    def __init__(self, root=None):
        self.root=root or (Path.home()/".companyos_runtime"/"learning_memory")
        self.root.mkdir(parents=True,exist_ok=True)

    def add(self, source_type, source_id, lesson, confidence=0.5, metadata=None):
        r=LearningRecord(str(uuid.uuid4()),source_type,source_id,lesson,max(0.0,min(1.0,float(confidence))),time.time(),dict(metadata or {}))
        (self.root/f"{r.learning_id}.json").write_text(json.dumps(asdict(r),indent=2,sort_keys=True)+"\n")
        return r
