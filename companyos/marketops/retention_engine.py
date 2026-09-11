class RetentionEngine:
    def evaluate(self, cohorts):
        out=[]
        for c in cohorts or []:
            retention=float(c.get("retention_rate",0))
            engagement=float(c.get("engagement",0))
            satisfaction=float(c.get("satisfaction",0))
            health=retention*0.5+engagement*0.25+satisfaction*0.25
            out.append({
                **c,
                "health_score":round(health,3),
                "churn_risk":health<0.45,
                "expansion_ready":health>0.8
            })
        return out
