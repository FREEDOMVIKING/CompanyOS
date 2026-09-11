from .closed_loop_revalidation_controller import ClosedLoopRevalidationController
class CEORevalidationExecutionBridge:
    """887: CEO-facing closed-loop revalidation execution bridge."""
    def __init__(self,root): self.controller=ClosedLoopRevalidationController(root)
    def run_round(self,*args,**kwargs): return self.controller.run_round(*args,**kwargs)
