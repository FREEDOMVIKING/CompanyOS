class GoalTree:
    """101: convert company goals into measurable objective trees."""
    def build(self, goal, objectives):
        nodes=[]
        for i,o in enumerate(objectives,1):
            nodes.append({"id":f"obj-{i}","goal":goal,"objective":o.get("objective",""),
            "metric":o.get("metric"),"target":o.get("target"),"status":"planned"})
        return {"goal":goal,"objectives":nodes,"count":len(nodes)}
