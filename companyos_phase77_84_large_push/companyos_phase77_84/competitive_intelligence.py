class CompetitiveIntelligence:
    """81: structured competitor-gap analysis."""
    def gaps(self,our_features,competitors):
        ours=set(our_features); counts={}
        for c in competitors:
            for f in c.get("features",[]): counts[f]=counts.get(f,0)+1
        missing=[{"feature":f,"competitor_count":n} for f,n in counts.items() if f not in ours]
        missing.sort(key=lambda x:x["competitor_count"],reverse=True)
        return {"missing_common_features":missing,"our_unique_features":[f for f in ours if counts.get(f,0)==0]}
