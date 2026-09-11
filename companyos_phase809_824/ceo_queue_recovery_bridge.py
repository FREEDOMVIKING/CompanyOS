from .queue_recovery_controller import QueueRecoveryController

class CEOQueueRecoveryBridge:
    """823: CEO-facing queue recovery interface."""

    def __init__(self, root):
        self.controller = QueueRecoveryController(root)

    def run_once(self, max_recoveries=3):
        return self.controller.run_once(max_recoveries=max_recoveries)
