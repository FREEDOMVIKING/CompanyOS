class PortfolioPriority:
    """684: portfolio-level priority score."""

    def score(self, venture):
        score=0.0
        score += float(venture.get("validation_score",0))*0.25
        score += min(10,float(venture.get("revenue_signal",0)))*0.2
        score += min(10,float(venture.get("roi_score",0)))*0.25
        score += min(10,float(venture.get("resource_efficiency",0))*2)*0.2
        score += min(10,float(venture.get("retention_rate",0))*10)*0.1
        score -= min(3.0,int(venture.get("stagnant_cycles",0))*0.6)
        return round(max(0.0,min(10.0,score)),2)
