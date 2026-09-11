class ValidationScorecard:
    """396: concise validation scorecard."""

    def build(self, thesis, interpretation, decision):
        return {
            "opportunity": thesis.get("name"),
            "customer": thesis.get("customer"),
            "validation_pass_ratio": interpretation.get("pass_ratio"),
            "checks": interpretation.get("checks"),
            "decision": decision,
        }
