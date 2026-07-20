from __future__ import annotations
from pathlib import Path
from .state_store import ImprovementStateStore

class ResumeController:
    """291: manual pause/resume/status controller for persistent loop."""

    def __init__(self, project_root):
        self.store = ImprovementStateStore(Path(project_root))

    def pause(self):
        state = self.store.load()
        state["paused"] = True
        self.store.save(state)
        return state

    def resume(self):
        state = self.store.load()
        state["paused"] = False
        self.store.save(state)
        return state

    def status(self):
        return self.store.load()
