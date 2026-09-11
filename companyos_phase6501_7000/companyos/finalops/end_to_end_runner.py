class EndToEndRunner:
    STAGES=["discover","research","validate","build","launch","operate","optimize","portfolio_review"]
    def run(self, available_stages):
        available=set(available_stages or [])
        rows=[]
        for s in self.STAGES:
            ok=s in available
            rows.append({"stage":s,"passed":ok})
        return {"passed":all(r["passed"] for r in rows),"stages":rows}
