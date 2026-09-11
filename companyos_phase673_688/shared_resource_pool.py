class SharedResourcePool:
    """676: shared specialist/resource pool across ventures."""

    def allocate(self, ventures, capacity=None):
        capacity = capacity or {"builder":2,"qa_reviewer":1,"growth_analyst":1,"product_manager":1}
        ordered = sorted(ventures, key=lambda v: float(v.get("priority_score",0)), reverse=True)
        allocations = {k:[] for k in capacity}
        for role, slots in capacity.items():
            for v in ordered[:max(0,int(slots))]:
                allocations[role].append(v.get("venture_id"))
        return {"capacity":capacity,"allocations":allocations}
