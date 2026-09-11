class KillScalePolicy:
    """569: evidence-based continue/iterate/scale/kill recommendation."""

    def decide(self, evidence):
        validation=float(evidence.get("validation_score",0))
        activation=float(evidence.get("activation_rate",0))
        retention=float(evidence.get("retention_rate",0))
        revenue=float(evidence.get("revenue_signal",0))
        failures=int(evidence.get("consecutive_failures",0))

        if failures >= 3 and retention < 0.1:
            action="kill_or_pause"
        elif validation >= 7 and activation >= 0.25 and retention >= 0.3 and revenue >= 3:
            action="scale"
        elif validation >= 5 and (activation >= 0.12 or retention >= 0.15):
            action="iterate"
        else:
            action="research_or_validate_more"
        return {"decision":action,"evidence":evidence}
