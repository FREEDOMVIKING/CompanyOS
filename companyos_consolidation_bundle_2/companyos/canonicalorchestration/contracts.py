from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List
import time
import uuid

@dataclass
class GoalRequest:
    objective: str
    context: Dict[str, Any] = field(default_factory=dict)
    source: str = "ceo_runtime"
    goal_id: str = ""
    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        if not self.goal_id:
            self.goal_id = str(uuid.uuid4())

    def to_dict(self):
        return asdict(self)

@dataclass
class TaskRecord:
    task_id: str
    goal_id: str
    name: str
    action: str
    payload: Dict[str, Any]
    requires_human_approval: bool = False
    external_action: bool = False
    financial_action: bool = False
    status: str = "queued"
    result: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)

@dataclass
class GoalRunResult:
    goal_id: str
    objective: str
    status: str
    tasks_total: int
    tasks_completed: int
    tasks_blocked: int
    tasks_failed: int
    task_results: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)
