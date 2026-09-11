from companyos_phase593_608 import HypothesisStore, StrategyState

class LearningProbe:
    """725: confirm strategic learning persistence."""

    def __init__(self, root):
        self.hypotheses=HypothesisStore(root)
        self.strategy=StrategyState(root)

    def inspect(self, venture_id):
        h=self.hypotheses.get(venture_id)
        s=self.strategy.load().get(venture_id,{})
        return {
            "venture_id":venture_id,
            "hypotheses_present":bool(h),
            "strategy_present":bool(s),
            "hypotheses":h,
            "strategy":s,
        }
