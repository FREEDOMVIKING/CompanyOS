class ChannelOptimizer:
    def rank(self, channels):
        rows=[]
        for c in channels or []:
            cac=float(c.get("cac",999))
            ltv=float(c.get("ltv",0))
            conv=float(c.get("conversion_rate",0))
            scale=float(c.get("scalability",0))
            quality=float(c.get("lead_quality",0))
            efficiency=(ltv/max(cac,1))
            score=min(1,efficiency/5)*0.3+conv*0.25+scale*0.2+quality*0.25
            rows.append({**c,"channel_score":round(score,4)})
        return sorted(rows,key=lambda x:x["channel_score"],reverse=True)
