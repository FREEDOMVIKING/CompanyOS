class EvidenceLearner:
    """169: update beliefs from observed results rather than static assumptions."""
    def update(self, beliefs, evidence):
        ev={}
        for e in evidence:
            topic=str(e.get("topic","general")); ev.setdefault(topic,[]).append(float(e.get("signal",0)))
        out=[]
        for b in beliefs:
            topic=str(b.get("topic","general")); prior=float(b.get("confidence",.5)); vals=ev.get(topic,[])
            observed=sum(vals)/len(vals) if vals else prior
            confidence=max(0,min(1,prior*.4+observed*.6))
            out.append({**b,"confidence":round(confidence,4),"evidence_count":len(vals)})
        return out
