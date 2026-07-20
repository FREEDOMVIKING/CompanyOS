from typing import Any, Dict, List
class ValidationEngine:
    """70: evidence-based opportunity validation."""
    def validate(self, evidence: List[Dict[str,Any]]):
        if not evidence:return {"verdict":"insufficient_evidence","confidence":0.0,"count":0}
        weighted=total=0.0
        for e in evidence:
            w=max(0,min(1,float(e.get("reliability",.5))))
            weighted+=max(-1,min(1,float(e.get("support",0))))*w; total+=w
        net=weighted/total if total else 0
        return {"verdict":"validated" if net>=.35 else "rejected" if net<=-.35 else "uncertain",
                "confidence":round(min(1,total/len(evidence)),4),"net_support":round(net,4),"count":len(evidence)}
