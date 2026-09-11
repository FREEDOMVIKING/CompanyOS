class MarketRadar:
    def scan(self, signals):
        rows=[]
        for s in signals or []:
            demand=float(s.get("demand",0)); growth=float(s.get("growth",0))
            urgency=float(s.get("urgency",0)); competition=float(s.get("competition",0))
            score=demand*.35+growth*.3+urgency*.2+(1-competition)*.15
            rows.append({**s,"market_score":round(max(0,min(1,score)),3)})
        return sorted(rows,key=lambda x:x["market_score"],reverse=True)
