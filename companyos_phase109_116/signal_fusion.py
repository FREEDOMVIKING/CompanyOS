class SignalFusion:
    """109: fuse multi-source business signals using confidence weighting."""
    def fuse(self,signals):
        total=weighted=0.0; sources=[]
        for s in signals:
            confidence=max(0,min(1,float(s.get("confidence",.5))))
            value=max(-1,min(1,float(s.get("value",0))))
            weighted+=value*confidence;total+=confidence
            sources.append(s.get("source","unknown"))
        return {"signal":round(weighted/total,4) if total else 0.0,
        "confidence":round(min(1,total/max(1,len(signals))),4),"sources":sources,"count":len(signals)}
