class MarketSignalEngine:
    def score(self, signals):
        rows=[]
        for s in signals or []:
            score=(
                float(s.get("demand",0))*0.25 +
                float(s.get("pain",0))*0.20 +
                float(s.get("urgency",0))*0.15 +
                float(s.get("budget",0))*0.15 +
                float(s.get("competition_gap",0))*0.15 +
                float(s.get("evidence_quality",0))*0.10
            )
            rows.append({**s,"market_score":round(score,4)})
        return sorted(rows,key=lambda x:x["market_score"],reverse=True)
