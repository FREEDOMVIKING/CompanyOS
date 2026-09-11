from dataclasses import dataclass, field
from typing import Any

@dataclass
class WorkOrder:
    id: str
    objective: str
    department: str
    priority: int = 5
    context: dict[str, Any] = field(default_factory=dict)
    status: str = "queued"

@dataclass
class DepartmentResult:
    department: str
    status: str
    findings: list[str] = field(default_factory=list)
    actions: list[dict] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)
