class StageEvidence:
    """563: define minimum evidence expected at each venture stage."""

    REQUIRED = {
        "research":["problem_signal","source_diversity"],
        "validation":["validation_decision","validation_score"],
        "build":["venture_packet","quality_contract"],
        "launch":["release_candidate_ready","rollback_ready","telemetry_ready"],
        "operations":["activation_rate","retention_rate"],
        "scale":["retention_rate","revenue_signal","unit_economics"],
    }

    def evaluate(self, stage, evidence):
        required = self.REQUIRED.get(stage, [])
        present = [k for k in required if evidence.get(k) not in (None,False,"")]
        return {
            "stage":stage,
            "ready":len(present)==len(required),
            "required":required,
            "present":present,
            "missing":[k for k in required if k not in present],
        }
