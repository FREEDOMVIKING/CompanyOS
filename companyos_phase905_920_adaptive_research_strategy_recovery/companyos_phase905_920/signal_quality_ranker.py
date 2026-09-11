class SignalQualityRanker:
    """911: rank evidence by decision usefulness."""
    WEIGHTS={"official":1.0,"reputable_news":0.85,"competitor_site":0.75,"public_web":0.65,"github":0.7,"hacker_news":0.45}
    def rank(self,evidence):
        rows=[]
        for e in evidence or []:
            r=dict(e)
            tags=set(r.get("tags",[]))
            tag_bonus=min(0.25,0.05*len(tags.intersection({"problem","demand","pricing","alternatives","risk"})))
            r["signal_quality"]=round(min(1.0,self.WEIGHTS.get(r.get("source_class"),0.4)+tag_bonus),3)
            rows.append(r)
        return sorted(rows,key=lambda x:x["signal_quality"],reverse=True)
