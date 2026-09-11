class GrowthMetricEngine:
    """1045-1052: activation, retention, conversion, and growth scoring."""
    def compute(self, metrics):
        m=metrics or {}
        activation=float(m.get("activation_rate",0))
        retention=float(m.get("retention_rate",0))
        conversion=float(m.get("conversion_rate",0))
        growth=float(m.get("growth_rate",0))
        score=activation*0.3+retention*0.35+conversion*0.2+max(0,growth)*0.15
        return {
            "activation_rate":activation,
            "retention_rate":retention,
            "conversion_rate":conversion,
            "growth_rate":growth,
            "growth_score":round(min(1.0,max(0.0,score)),3),
        }
