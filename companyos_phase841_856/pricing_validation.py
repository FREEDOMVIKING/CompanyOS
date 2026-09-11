class PricingValidation:
    """846: score pricing/willingness-to-pay evidence."""
    def score(self, packet):
        evidence=list((packet or {}).get("evidence") or [])
        pricing=sum(1 for e in evidence if "pricing" in e.get("tags",[]))
        signals=sum(float(e.get("willingness_to_pay_score",0)) for e in evidence)
        base = (pricing / max(1,len(evidence))) * 0.7
        if signals:
            base += min(0.3, signals/max(1,len(evidence))*0.3)
        return round(min(1.0,base),3)
