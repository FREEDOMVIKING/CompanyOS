class ConnectorHealthRouter:
    def rank(self, connectors, health):
        hmap={x.get("name"):x for x in health or []}
        rows=[]
        for c in connectors or []:
            h=hmap.get(c.get("name"),{})
            availability=float(h.get("availability",1))
            error_rate=float(h.get("error_rate",0))
            latency=float(h.get("latency_score",.8))
            quality=float(h.get("quality",.8))
            score=availability*.35+(1-error_rate)*.25+latency*.15+quality*.25
            rows.append({**c,"health_score":round(score,3)})
        return sorted(rows,key=lambda x:(x["health_score"],x.get("priority",0)),reverse=True)
