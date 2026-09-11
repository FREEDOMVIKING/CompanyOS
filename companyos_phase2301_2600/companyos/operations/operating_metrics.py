class OperatingMetrics:
    def score(self, metrics):
        m=metrics or {}
        weights={
            "revenue_growth":0.2,
            "retention_rate":0.2,
            "gross_margin":0.15,
            "conversion_rate":0.15,
            "reliability":0.15,
            "customer_satisfaction":0.15
        }
        score=0.0
        for k,w in weights.items():
            score+=float(m.get(k,0))*w
        return {"operating_score":round(max(0,min(1,score)),3),"signals":m}
