class AllocationPolicy:
    """667: scale/maintain/constrain/pause recommendation."""

    def decide(self, venture):
        roi=float(venture.get("roi_score",0))
        efficiency=float(venture.get("resource_efficiency",0))
        anomalies=venture.get("has_anomaly",False)
        runway=venture.get("runway_months")
        if anomalies and roi < 4:
            action="pause_or_constrain"
        elif runway is not None and runway < 3:
            action="constrain_and_extend_runway"
        elif roi >= 7 and efficiency >= 1:
            action="prepare_scale_review"
        elif roi >= 4:
            action="maintain_and_optimize"
        else:
            action="reduce_or_revalidate"
        return {
            "decision":action,
            "automatic_financial_transfer":False,
            "automatic_purchase":False,
            "requires_explicit_financial_approval":True,
        }
