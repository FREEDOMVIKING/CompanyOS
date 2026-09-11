class PortfolioDecision:
    """426: evidence-based scale/pivot/kill/hold recommendation."""

    def decide(self, evidence):
        activation = float(evidence.get("activation_rate",0))
        retention = float(evidence.get("retention_rate",0))
        paid = float(evidence.get("trial_to_paid",0))

        if activation >= .35 and retention >= .25 and paid >= .05:
            decision = "scale"
        elif activation >= .15 or retention >= .10:
            decision = "iterate"
        elif evidence.get("sample_size",0) < 20:
            decision = "hold_for_more_evidence"
        else:
            decision = "pivot_or_kill"

        return {"decision":decision, "evidence":evidence}
