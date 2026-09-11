class ScaleDecision:
    """461: decide scale/iterate/hold/pivot based on operating evidence."""

    def decide(self, evidence):
        activation = float(evidence.get("activation_rate",0))
        retention = float(evidence.get("gross_retention",0))
        growth = float(evidence.get("mrr_growth_rate",0))
        ltv_cac = evidence.get("ltv_cac_ratio")

        if activation >= 0.35 and retention >= 0.75 and growth > 0 and (ltv_cac is None or ltv_cac >= 3):
            action = "scale"
        elif activation >= 0.15 and retention >= 0.50:
            action = "iterate"
        elif evidence.get("sample_size",0) < 30:
            action = "hold_for_more_evidence"
        else:
            action = "pivot_or_kill"
        return {"decision":action,"evidence":evidence}
