class HealthMatrix:
    def evaluate(self, components):
        rows=[]
        for c in components or []:
            heartbeat=bool(c.get("heartbeat",True))
            error_rate=float(c.get("error_rate",0))
            saturation=float(c.get("saturation",0))
            backlog=int(c.get("backlog",0))
            score=(1 if heartbeat else 0)*.35 + max(0,1-error_rate)*.25 + max(0,1-saturation)*.2 + max(0,1-backlog/100)*.2
            rows.append({**c,"health_score":round(score,3),"healthy":score>=.7})
        overall=sum(x["health_score"] for x in rows)/max(1,len(rows))
        return {"overall_health":round(overall,3),"healthy":overall>=.7,"components":rows}
