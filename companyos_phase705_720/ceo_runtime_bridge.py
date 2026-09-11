from .runtime_supervisor import RuntimeSupervisor
from .portfolio_bridge import PortfolioBridge
from .system_registry import SystemRegistry

class CEORuntimeBridge:
    """719: CEO-facing unified runtime interface."""

    def __init__(self, root):
        self.supervisor = RuntimeSupervisor(root)

    def tick(self):
        return self.supervisor.tick()

    def portfolio_review(self, ventures):
        return PortfolioBridge().review(ventures)

    def systems(self):
        return SystemRegistry().describe()
