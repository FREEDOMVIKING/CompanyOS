from pathlib import Path
from .service_config import ServiceConfig
from .service_state import ServiceState
from .service_lock import ServiceLock
from .service_journal import ServiceJournal
from .startup_recovery import StartupRecovery
from .service_loop import ServiceLoop

class AutonomousCEOService:
    """559: one-command persistent CEO service."""

    def __init__(self, root):
        self.root = Path(root).resolve()
        self.config = ServiceConfig().load()
        self.state_store = ServiceState(self.root)
        self.lock = ServiceLock(self.root)
        self.journal = ServiceJournal(self.root)

    def run(self, max_ticks=None):
        lock = self.lock.acquire()
        if not lock["acquired"]:
            return {"success":False,"status":"ceo_service_already_running","lock":lock}

        try:
            state = StartupRecovery().recover(self.state_store.load())
            self.state_store.save(state)
            self.journal.append("service_start", {"max_ticks":max_ticks})
            return ServiceLoop(
                self.root,
                self.config,
                self.state_store,
                self.journal,
            ).run(max_ticks=max_ticks)
        finally:
            self.lock.release()
            self.journal.append("service_stop", {})
