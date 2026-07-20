from __future__ import annotations
from pathlib import Path
from .state_store import ImprovementStateStore
from .adaptive_scheduler import AdaptiveScheduler

class PersistentRuntime:
    """292: persistent self-improvement runtime status."""

    def __init__(self, project_root):
        self.root = Path(project_root).resolve()

    def status(self):
        return {
            "success": True,
            "status": "phase292_persistent_self_improvement_ready",
            "state": ImprovementStateStore(self.root).load(),
            "default_delay_seconds": AdaptiveScheduler().next_delay(True),
            "durable_resume_state": True,
            "append_only_cycle_journal": True,
            "pause_resume_control": True,
            "verification_gates_preserved": True,
            "autonomy_mode": "high",
        }
