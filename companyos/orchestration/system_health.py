class UnifiedSystemHealth:
    def evaluate(self, systems):
        rows=[]
        for s in systems or []:
            healthy=bool(s.get("healthy",True))
            failures=int(s.get("consecutive_failures",0))
            backlog=int(s.get("backlog",0))
            score=(1 if healthy else 0)*.5 + max(0,1-failures/5)*.25 + max(0,1-backlog/100)*.25
            rows.append({**s,"health_score":round(score,3),
                         "action":"keep_running" if score>=.7 else ("repair" if score>=.4 else "isolate_and_recover")})
        overall=sum(x["health_score"] for x in rows)/max(1,len(rows))
        return {"overall_health":round(overall,3),"systems":rows,"healthy":overall>=.7}
