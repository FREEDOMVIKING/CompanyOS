class ValidationGapAnalyzer:
    def analyze(self, validation):
        scores=dict(validation.get("scores") or {})
        gaps=[]
        for key,target in (("problem_evidence",0.65),("pricing_validation",0.60),("validation_confidence",0.72)):
            value=float(scores.get(key,0) or 0)
            if value<target: gaps.append({"dimension":key,"score":value,"target":target,"gap":round(target-value,3)})
        if not (validation.get("contradictions") or {}).get("resolved",True):
            gaps.append({"dimension":"contradictions","score":0,"target":1,"gap":1})
        return sorted(gaps,key=lambda x:x["gap"],reverse=True)
