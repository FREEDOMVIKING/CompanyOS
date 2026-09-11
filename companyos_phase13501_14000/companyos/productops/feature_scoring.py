class FeatureScoringEngine:
    def score(self, features):
        out=[]
        for f in features or []:
            reach=float(f.get("reach",0))
            impact=float(f.get("impact",0))
            confidence=float(f.get("confidence",0))
            effort=max(.1,float(f.get("effort",1)))
            score=(reach*impact*confidence)/effort
            out.append({**f,"rice_like_score":round(score,4)})
        return sorted(out,key=lambda x:x["rice_like_score"],reverse=True)
