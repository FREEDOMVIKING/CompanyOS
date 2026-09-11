class ScaleAllocator:
    def allocate(self, opportunities, budget):
        rows=[]
        for o in opportunities or []:
            roi=float(o.get("expected_roi",0))
            confidence=float(o.get("confidence",0.5))
            capacity=float(o.get("capacity",1))
            score=max(0,roi*confidence*capacity)
            rows.append({**o,"scale_score":round(score,4)})
        rows=sorted(rows,key=lambda x:x["scale_score"],reverse=True)
        total=sum(r["scale_score"] for r in rows) or 1
        return [
            {"name":r.get("name"),"allocation":round(float(budget)*(r["scale_score"]/total),2),"score":r["scale_score"]}
            for r in rows
        ]
