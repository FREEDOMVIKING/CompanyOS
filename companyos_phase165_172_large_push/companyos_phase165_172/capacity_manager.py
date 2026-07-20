class CapacityManager:
    """171: protect continuous operation by reserving capacity for repair and exploration."""
    def allocate(self,total,operations=.55,growth=.25,exploration=.10,resilience=.10):
        total=max(0,float(total)); weights=[max(0,float(x)) for x in (operations,growth,exploration,resilience)]
        denom=sum(weights) or 1
        names=("operations","growth","exploration","resilience")
        return {n:round(total*w/denom,4) for n,w in zip(names,weights)}
