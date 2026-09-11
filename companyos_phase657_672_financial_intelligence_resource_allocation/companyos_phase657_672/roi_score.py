class ROIScore:
    """662: normalize ROI into a 0-10 score."""

    def score(self, metrics):
        gain=float(metrics.get("incremental_value",0))
        cost=float(metrics.get("resource_cost",0))
        if cost <= 0:
            return 10.0 if gain > 0 else 0.0
        roi=(gain-cost)/cost
        return round(max(0.0,min(10.0,(roi+1)*5)),2)
