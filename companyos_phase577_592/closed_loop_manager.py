from .venture_feedback_loop import VentureFeedbackLoop
from .lifecycle_store import LifecycleStore
from .lifecycle_audit import LifecycleAudit

class ClosedLoopManager:
    """589: persist outcome, stage transition, and next mission."""

    def __init__(self, root):
        self.store = LifecycleStore(root)
        self.audit = LifecycleAudit(root)

    def apply_outcome(self, venture_id, outcome):
        record = self.store.get(venture_id) or {
            "venture_id":venture_id,
            "stage":"research",
            "evidence":{},
            "stagnant_cycles":0,
        }

        result = VentureFeedbackLoop().update(record, outcome)
        self.store.upsert(venture_id, result["record"])
        self.audit.append(venture_id, "outcome_applied", {
            "before_stage":result["before_stage"],
            "after_stage":result["after_stage"],
            "outcome_score":result["outcome_score"],
            "next_action":result["next_action"],
        })
        return result
