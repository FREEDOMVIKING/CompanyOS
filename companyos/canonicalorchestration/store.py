from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import json

class OrchestrationStore:
    def __init__(self, runtime_root: Path):
        self.root = runtime_root / "canonical_orchestration"
        self.goals = self.root / "goals"
        self.tasks = self.root / "tasks"
        self.root.mkdir(parents=True, exist_ok=True)
        self.goals.mkdir(parents=True, exist_ok=True)
        self.tasks.mkdir(parents=True, exist_ok=True)
        self.journal = self.root / "journal.jsonl"

    def write_goal(self, goal_id: str, data: Dict[str, Any]) -> None:
        (self.goals / f"{goal_id}.json").write_text(
            json.dumps(data, indent=2, sort_keys=True)
        )

    def write_task(self, task_id: str, data: Dict[str, Any]) -> None:
        (self.tasks / f"{task_id}.json").write_text(
            json.dumps(data, indent=2, sort_keys=True)
        )

    def append(self, event: str, data: Dict[str, Any]) -> None:
        with self.journal.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"event": event, "data": data}, sort_keys=True) + "\n")

    def summary(self) -> Dict[str, Any]:
        return {
            "goals": len(list(self.goals.glob("*.json"))),
            "tasks": len(list(self.tasks.glob("*.json"))),
            "journal_present": self.journal.exists(),
        }
