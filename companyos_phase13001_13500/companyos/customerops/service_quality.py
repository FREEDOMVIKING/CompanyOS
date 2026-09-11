class ServiceQualityEngine:
    def score(self, signals):
        keys=["resolution_rate","satisfaction","sla_rate","first_contact_resolution"]
        vals=[float(signals.get(k,0)) for k in keys]
        score=sum(vals)/len(vals)
        return {"service_quality_score":round(score,4),"healthy":score>=.8}
