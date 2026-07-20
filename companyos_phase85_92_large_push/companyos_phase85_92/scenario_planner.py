class ScenarioPlanner:
    """89: best/base/worst-case planning."""
    def build(self,base_value,upside=.25,downside=.25):
        base=float(base_value)
        return {"worst":round(base*(1-max(0,float(downside))),2),
                "base":round(base,2),"best":round(base*(1+max(0,float(upside))),2)}
