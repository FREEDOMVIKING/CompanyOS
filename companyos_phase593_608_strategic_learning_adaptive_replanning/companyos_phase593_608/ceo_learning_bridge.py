from .hypothesis_store import HypothesisStore
from .strategy_state import StrategyState
from .adaptive_replanner import AdaptiveReplanner
from .learning_audit import LearningAudit

class CEOLearningBridge:
    """606: CEO-facing persistent strategic learning bridge."""

    def __init__(self, root):
        self.hypotheses = HypothesisStore(root)
        self.strategy = StrategyState(root)
        self.audit = LearningAudit(root)

    def apply(self, venture_id, before_stage, after_stage, outcome, next_mission, confidence=0.5):
        prior_h = self.hypotheses.get(venture_id)
        prior_s = self.strategy.load().get(venture_id,{})
        result = AdaptiveReplanner().replan(
            before_stage, after_stage, outcome,
            prior_h, prior_s, next_mission, confidence
        )
        self.hypotheses.put(venture_id, result["hypotheses"])
        self.strategy.put(venture_id, result["strategy"])
        self.audit.append(
            venture_id,
            result["lessons"],
            result["strategy"],
            result["rewritten_mission"],
        )
        return result
