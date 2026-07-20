class ProcessOptimizer:
    """87: identify bottlenecks from process telemetry."""
    def analyze(self,steps):
        rows=[]
        for s in steps:
            duration=max(0,float(s.get("duration",0))); failures=max(0,int(s.get("failures",0)))
            volume=max(1,int(s.get("volume",1)))
            penalty=duration*(1+failures/volume)
            rows.append({**s,"bottleneck_score":round(penalty,4)})
        rows.sort(key=lambda x:x["bottleneck_score"],reverse=True)
        return {"bottlenecks":rows,"top_bottleneck":rows[0] if rows else None}
