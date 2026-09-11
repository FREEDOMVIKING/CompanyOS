from .decision_policy import DecisionPolicy
from .junk_rejector import JunkRejector

class OpportunityDecisionBrain:
    """524: final autonomous decision brain for opportunity candidates."""

    def evaluate(self, candidate):
        junk = JunkRejector().decide(candidate)
        if junk["rejected"]:
            return {
                "decision":"reject",
                "quality_score":candidate.get("quality_score"),
                "reasons":junk["reasons"],
            }
        decision = DecisionPolicy().decide(candidate)
        return {**decision,"reasons":[]}
