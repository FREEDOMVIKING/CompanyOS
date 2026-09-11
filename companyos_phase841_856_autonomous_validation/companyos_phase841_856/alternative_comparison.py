class AlternativeComparison:
    """847: compare alternatives/competitors and differentiation signals."""
    def evaluate(self, packet):
        evidence=list((packet or {}).get("evidence") or [])
        alternatives=sum(1 for e in evidence if "alternatives" in e.get("tags",[]))
        competitors=sum(1 for e in evidence if e.get("source_class") in ("competitor_site","github"))
        return {
            "alternative_evidence_count":alternatives,
            "competitor_signal_count":competitors,
            "differentiation_risk":"high" if alternatives==0 else "moderate",
        }
