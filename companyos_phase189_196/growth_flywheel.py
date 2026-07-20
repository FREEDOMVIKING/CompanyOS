class GrowthFlywheel:
    """195: convert evidence, product quality, distribution, and retention into next growth focus."""
    def evaluate(self,state):
        dimensions={k:float(state.get(k,0)) for k in ("evidence","product","distribution","retention")}
        weakest=min(dimensions,key=dimensions.get)
        return {"dimensions":dimensions,"constraint":weakest,
                "next_focus":f"improve:{weakest}","autonomous":True}
