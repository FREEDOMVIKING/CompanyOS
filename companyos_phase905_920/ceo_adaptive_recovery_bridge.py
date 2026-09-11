from .adaptive_recovery_controller import AdaptiveRecoveryController
class CEOAdaptiveRecoveryBridge:
    """919: CEO-facing adaptive stalled-revalidation recovery."""
    def __init__(self,root): self.controller=AdaptiveRecoveryController(root)
    def build_strategy(self,*args,**kwargs): return self.controller.build_strategy(*args,**kwargs)
