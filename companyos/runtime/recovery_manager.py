from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json

@dataclass(frozen=True)
class RecoverySummary:
    projects_scanned: int
    blocked_projects: int
    recoverable_projects: int

class RecoveryManager:
    def __init__(self, projects_root=None):
        self.projects_root = projects_root or (Path.home()/".companyos_runtime"/"projects")

    def scan(self):
        total=blocked=recoverable=0
        if self.projects_root.exists():
            for p in self.projects_root.glob("*.json"):
                try:
                    d=json.loads(p.read_text()); total+=1
                    if d.get("stage")=="BLOCKED":
                        blocked+=1
                    elif d.get("state")=="ACTIVE":
                        recoverable+=1
                except Exception:
                    pass
        return RecoverySummary(total,blocked,recoverable)
