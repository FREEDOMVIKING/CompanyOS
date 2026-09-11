from .launch_readiness import LaunchReadiness
from .business_ops_manager import BusinessOpsManager

class CEOOperationsBridge:
    """463: bridge release readiness into measured business operations."""

    def launch_review(self, state):
        return LaunchReadiness().evaluate(state)

    def operating_review(self, metrics):
        return BusinessOpsManager().review(metrics)
