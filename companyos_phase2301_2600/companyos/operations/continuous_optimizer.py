class ContinuousBusinessOptimizer:
    def recommend(self, metrics):
        m=metrics or {}
        actions=[]
        if float(m.get("retention_rate",0))<0.5:
            actions.append("improve_retention")
        if float(m.get("conversion_rate",0))<0.05:
            actions.append("improve_conversion")
        if float(m.get("gross_margin",0))<0.5:
            actions.append("improve_margin")
        if float(m.get("incident_rate",0))>0.05:
            actions.append("stabilize_reliability")
        if not actions:
            actions.append("scale_best_channel")
        return actions
