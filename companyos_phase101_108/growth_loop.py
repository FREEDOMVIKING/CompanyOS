class GrowthLoop:
    """106: choose growth experiments from measured funnel gaps."""
    def recommend(self,metrics):
        acquisition=float(metrics.get("acquisition",0)); activation=float(metrics.get("activation",0))
        retention=float(metrics.get("retention",0)); referral=float(metrics.get("referral",0))
        vals={"acquisition":acquisition,"activation":activation,"retention":retention,"referral":referral}
        weakest=min(vals,key=vals.get) if vals else None
        return {"weakest_stage":weakest,"recommendation":f"design_experiment_for_{weakest}" if weakest else None,
        "auto_external_execution":False}
