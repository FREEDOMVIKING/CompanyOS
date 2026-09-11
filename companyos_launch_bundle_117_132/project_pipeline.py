from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


@dataclass
class ProjectRecord:
    project_id: str
    title: str
    objective: str
    source_goal_id: str | None
    source_opportunity_id: str | None
    state: str
    stage: str
    priority: int
    created_at_unix: float
    updated_at_unix: float
    artifacts: list[str]
    blockers: list[str]
    metadata: dict[str, Any]


class ProjectPipeline:
    """
    Durable internal opportunity/goal -> project pipeline.

    States/stages are internal planning/build states only.
    No external publish/deploy/purchase actions are performed here.
    """

    STAGES = [
        "DISCOVERY",
        "VALIDATION",
        "PLANNING",
        "BUILD",
        "QA",
        "LAUNCH_READY",
        "COMPLETED",
        "BLOCKED",
        "FAILED",
    ]

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or (Path.home() / ".companyos_runtime" / "projects")
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, project_id: str) -> Path:
        return self.root / f"{project_id}.json"

    def save(self, record: ProjectRecord) -> None:
        path = self._path(record.project_id)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(asdict(record), indent=2, sort_keys=True) + "\n")
        tmp.replace(path)

    def load(self, project_id: str) -> ProjectRecord:
        return ProjectRecord(**json.loads(self._path(project_id).read_text()))

    def all(self) -> list[ProjectRecord]:
        out = []
        for p in self.root.glob("*.json"):
            try:
                out.append(self.load(p.stem))
            except Exception:
                pass
        return out

    def create(
        self,
        *,
        title: str,
        objective: str,
        source_goal_id: str | None = None,
        source_opportunity_id: str | None = None,
        priority: int = 100,
        metadata: dict[str, Any] | None = None,
    ) -> ProjectRecord:
        now = time.time()
        rec = ProjectRecord(
            project_id=str(uuid.uuid4()),
            title=title.strip(),
            objective=objective.strip(),
            source_goal_id=source_goal_id,
            source_opportunity_id=source_opportunity_id,
            state="ACTIVE",
            stage="DISCOVERY",
            priority=int(priority),
            created_at_unix=now,
            updated_at_unix=now,
            artifacts=[],
            blockers=[],
            metadata=dict(metadata or {}),
        )
        self.save(rec)
        return rec

    def advance(self, project_id: str) -> ProjectRecord:
        rec = self.load(project_id)
        if rec.stage in ("COMPLETED", "BLOCKED", "FAILED"):
            return rec
        idx = self.STAGES.index(rec.stage)
        next_stage = self.STAGES[min(idx + 1, len(self.STAGES) - 1)]
        rec.stage = next_stage
        if next_stage == "COMPLETED":
            rec.state = "COMPLETED"
        rec.updated_at_unix = time.time()
        self.save(rec)
        return rec
