from companyos_phase529_544 import CEOQualityScheduler

class QualityTick:
    """547: run one quality-aware opportunity/scheduler integration cycle."""

    def __init__(self, root):
        self.runner = CEOQualityScheduler(root)

    def run(self):
        return self.runner.run()
