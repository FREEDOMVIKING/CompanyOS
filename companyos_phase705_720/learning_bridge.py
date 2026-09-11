from companyos_phase593_608 import CEOLearningBridge

class LearningBridge:
    """712: strategic learning from lifecycle transitions and outcomes."""

    def __init__(self, root):
        self.bridge = CEOLearningBridge(root)

    def apply(self, venture_id, lifecycle_result, outcome):
        return self.bridge.apply(
            venture_id,
            lifecycle_result.get("before_stage"),
            lifecycle_result.get("after_stage"),
            outcome,
            lifecycle_result.get("next_mission"),
            confidence=0.5,
        )
