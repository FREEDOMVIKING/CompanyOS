class CampaignAllocator:
    """1141-1150: allocate growth budget with bounded risk."""
    def allocate(self, campaigns, budget, max_share=0.4):
        eligible=[c for c in (campaigns or []) if c.get("enabled",True)]
        total_score=sum(max(0,float(c.get("score",0))) for c in eligible) or 1
        allocations=[]
        remaining=float(budget)
        for c in sorted(eligible,key=lambda x:float(x.get("score",0)),reverse=True):
            raw=float(budget)*(max(0,float(c.get("score",0)))/total_score)
            capped=min(raw,float(budget)*float(max_share),remaining)
            allocations.append({"campaign":c.get("name"),"allocation":round(capped,2)})
            remaining-=capped
        return {"allocations":allocations,"reserve":round(max(0,remaining),2)}
