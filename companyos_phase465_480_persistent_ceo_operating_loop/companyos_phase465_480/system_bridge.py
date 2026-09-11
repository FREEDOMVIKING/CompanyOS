from .opportunity_stage import OpportunityStage
from .validation_stage import ValidationStage
from .venture_stage import VentureStage
from .build_stage import BuildStage
from .operations_stage import OperationsStage
from .portfolio_stage import PortfolioStage

class SystemBridge:
    """477: bridge all previously-built subsystems under one stage interface."""

    def __init__(self, root):
        self.stages = {
            "opportunity": OpportunityStage(root),
            "validation": ValidationStage(),
            "venture": VentureStage(),
            "build": BuildStage(),
            "operations": OperationsStage(),
            "portfolio": PortfolioStage(),
        }

    def run_stage(self, stage, context=None):
        handler = self.stages.get(stage)
        if not handler:
            return {"success":False,"status":"unknown_stage","stage":stage,"data":{}}
        return handler.run(context or {})
