from .stage_evidence import StageEvidence

class CommitmentGate:
    """564: prevent major commitment before evidence is sufficient."""

    def evaluate(self, stage, evidence):
        gate = StageEvidence().evaluate(stage, evidence)
        return {
            **gate,
            "commitment_allowed": gate["ready"],
            "automatic_financial_commitment": False,
            "automatic_irreversible_external_action": False,
        }
