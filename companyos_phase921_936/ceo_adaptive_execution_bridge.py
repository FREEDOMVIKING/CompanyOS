from .adaptive_closed_loop_controller import AdaptiveClosedLoopController
class CEOAdaptiveExecutionBridge:
    """934: CEO-facing adaptive strategy execution and feedback bridge."""
    def __init__(self,root): self.controller=AdaptiveClosedLoopController(root)
    def run(self,*args,**kwargs): return self.controller.run(*args,**kwargs)
