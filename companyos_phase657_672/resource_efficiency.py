class ResourceEfficiency:
    """663: measure value created per unit of attention/resource."""

    def score(self, venture):
        progress=float(venture.get("progress_score",0))
        cost=max(1.0,float(venture.get("resource_cost",1)))
        revenue=float(venture.get("revenue_signal",0))
        return round((progress*0.6 + revenue*0.4)/cost,4)
