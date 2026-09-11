class ProviderHealthRegistry:
    def rank(self, providers):
        rows=[]
        for p in providers or []:
            score=(
                float(p.get("availability",1))*0.4+
                (1-min(1,float(p.get("error_rate",0))))*0.25+
                float(p.get("quality",0.5))*0.25+
                float(p.get("freshness",0.5))*0.1
            )
            rows.append({**p,"health_score":round(score,3)})
        return sorted(rows,key=lambda x:x["health_score"],reverse=True)
