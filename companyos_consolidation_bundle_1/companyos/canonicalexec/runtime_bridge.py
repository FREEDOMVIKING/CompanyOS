from .contracts import ExecutionRequest
from .gateway import CanonicalExecutionGateway

class CanonicalRuntimeBridge:
    def __init__(self, companyos_root=None):
        self.gateway = CanonicalExecutionGateway(companyos_root)
    def submit(self, action, payload=None, **flags):
        req = ExecutionRequest(action=action, payload=payload or {}, **flags)
        return self.gateway.execute(req).to_dict()
