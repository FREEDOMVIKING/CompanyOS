class VentureScorecard:
    """562: normalized venture quality score."""

    def score(self, evidence):
        dims = {
            "validation": float(evidence.get("validation_score",0)),
            "activation": min(10.0, float(evidence.get("activation_rate",0))*20),
            "retention": min(10.0, float(evidence.get("retention_rate",0))*12.5),
            "revenue": min(10.0, float(evidence.get("revenue_signal",0))*1.5),
            "quality": max(0.0, 10.0 - float(evidence.get("critical_issues",0))*2),
        }
        weights = {"validation":0.25,"activation":0.2,"retention":0.2,"revenue":0.2,"quality":0.15}
        total = sum(dims[k]*weights[k] for k in weights)
        return {"score":round(total,2),"dimensions":dims}
