from .venture_identity import VentureIdentity
from .lifecycle_store import LifecycleStore
from .closed_loop_manager import ClosedLoopManager
from .portfolio_feedback import PortfolioFeedback

class CEOLifecycleBridge:
    """590: CEO-facing lifecycle and outcome feedback bridge."""

    def __init__(self, root):
        self.root = root
        self.store = LifecycleStore(root)
        self.manager = ClosedLoopManager(root)

    def ensure_venture(self, name, theme=None, stage="research", evidence=None):
        venture_id = VentureIdentity().make(name, theme)
        record = {
            "venture_id":venture_id,
            "name":name,
            "theme":theme,
            "stage":stage,
            "evidence":dict(evidence or {}),
            "stagnant_cycles":0,
        }
        self.store.upsert(venture_id, record)
        return record

    def apply_outcome(self, venture_id, outcome):
        return self.manager.apply_outcome(venture_id, outcome)

    def portfolio_feedback(self):
        return PortfolioFeedback().analyze(list(self.store.load().values()))
