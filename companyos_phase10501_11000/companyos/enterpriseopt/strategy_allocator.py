class StrategyAllocator:
    def allocate(self, initiatives, max_parallel=5):
        rows=[]
        for i in initiatives or []:
            impact=float(i.get("impact",0))
            confidence=float(i.get("confidence",.5))
            alignment=float(i.get("alignment",.5))
            effort=max(.1,float(i.get("effort",1)))
            risk=float(i.get("risk",0))
            score=(impact*confidence*alignment*(1-risk))/effort
            rows.append({**i,"strategy_score":round(score,4)})
        return sorted(rows,key=lambda x:x["strategy_score"],reverse=True)[:int(max_parallel)]
