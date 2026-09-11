class ChannelAllocator:
    def allocate(self, channels, budget):
        scored=[]
        for c in channels or []:
            roi=max(0,float(c.get("roi",0))); confidence=float(c.get("confidence",.5))
            capacity=float(c.get("capacity",1)); score=roi*confidence*capacity
            scored.append({**c,"score":score})
        total=sum(x["score"] for x in scored) or 1
        return [{"channel":x.get("channel"),"allocation":round(float(budget)*x["score"]/total,2)}
                for x in sorted(scored,key=lambda y:y["score"],reverse=True)]
