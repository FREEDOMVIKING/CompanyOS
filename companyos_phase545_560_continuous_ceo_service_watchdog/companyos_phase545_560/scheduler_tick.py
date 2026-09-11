from companyos_phase497_512 import CEOSchedulerBridge

class SchedulerTick:
    """548: run one autonomous scheduler tick."""

    def __init__(self, root):
        self.runner = CEOSchedulerBridge(root)

    def run(self):
        return self.runner.run_tick()
