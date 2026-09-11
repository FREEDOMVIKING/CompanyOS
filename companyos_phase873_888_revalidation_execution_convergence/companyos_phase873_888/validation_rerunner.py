from companyos_phase841_856 import CEOValidationRuntimeBridge
class ValidationRerunner:
    """878: rerun validation after new evidence arrives."""
    def __init__(self,root): self.bridge=CEOValidationRuntimeBridge(root)
    def run(self,mission): return self.bridge.run(mission)
