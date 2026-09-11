from .multi_round_controller import MultiRoundRevalidationController
class CEOMultiRoundBridge:
    """902: CEO-facing autonomous multi-round bridge."""
    def __init__(self,root): self.controller=MultiRoundRevalidationController(root)
    def run(self,*args,**kwargs): return self.controller.run(*args,**kwargs)
