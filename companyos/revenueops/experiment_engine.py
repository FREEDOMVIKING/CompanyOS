class GrowthExperimentEngine:
    def prioritize(self, experiments):
        out=[]
        for e in experiments or []:
            score=float(e.get("impact",0))*float(e.get("confidence",0))/max(.1,float(e.get("effort",1)))
            out.append({**e,"ice_score":round(score,4)})
        return sorted(out,key=lambda x:x["ice_score"],reverse=True)
