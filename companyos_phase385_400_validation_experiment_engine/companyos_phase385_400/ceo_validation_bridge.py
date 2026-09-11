from .validation_orchestrator import ValidationOrchestrator
from .result_interpreter import ResultInterpreter
from .go_nogo_engine import GoNoGoEngine
from .validation_scorecard import ValidationScorecard

class CEOValidationBridge:
    """399: bridge from opportunity thesis to validation decision."""

    def __init__(self):
        self.orchestrator = ValidationOrchestrator()
        self.interpreter = ResultInterpreter()
        self.decision = GoNoGoEngine()
        self.scorecard = ValidationScorecard()

    def prepare(self, thesis):
        return self.orchestrator.plan(thesis)

    def evaluate(self, thesis, metrics):
        plan = self.orchestrator.plan(thesis)
        interpretation = self.interpreter.interpret(metrics, plan["thresholds"])
        decision = self.decision.decide(interpretation)
        return {
            "success": True,
            "status": "validation_evaluated",
            "plan": plan,
            "interpretation": interpretation,
            "decision": decision,
            "scorecard": self.scorecard.build(thesis, interpretation, decision),
        }
