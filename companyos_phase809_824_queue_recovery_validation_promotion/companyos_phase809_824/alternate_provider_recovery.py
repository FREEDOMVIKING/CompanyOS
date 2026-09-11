from companyos_phase793_808 import CEOResearchExecutionBridge

class AlternateProviderRecovery:
    """814: rerun deferred research through live multi-provider execution."""

    def __init__(self, root):
        self.bridge = CEOResearchExecutionBridge(root)

    def recover(self, mission):
        return self.bridge.process(mission, {})
