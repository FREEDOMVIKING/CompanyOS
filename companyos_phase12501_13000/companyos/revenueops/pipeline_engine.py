class RevenuePipelineEngine:
    def summarize(self, leads):
        stages={}
        value=0.0
        for l in leads or []:
            stage=l.get("stage","unknown"); stages[stage]=stages.get(stage,0)+1
            value+=float(l.get("expected_value",0))*float(l.get("probability",0))
        return {"stages":stages,"weighted_pipeline":round(value,2),"lead_count":len(leads or [])}
