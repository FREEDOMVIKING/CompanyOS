from companyos_phase577_592 import CEOLifecycleBridge

class LifecycleBridge:
    """711: persist outcome into venture lifecycle and generate next mission."""

    def __init__(self, root):
        self.bridge = CEOLifecycleBridge(root)

    def apply(self, venture_id, outcome):
        return self.bridge.apply_outcome(venture_id, outcome)
