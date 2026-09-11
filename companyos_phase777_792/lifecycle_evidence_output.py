class LifecycleEvidenceOutput:
    """791: convert final research packet into lifecycle evidence."""
    def build(self, packet):
        complete=bool((packet.get("completeness") or {}).get("complete"))
        confidence=float(packet.get("confidence",0))
        return {
            "validation_candidate_ready": complete and confidence >= 0.7,
            "research_confidence":confidence,
            "research_complete":complete,
            "source_diversified":bool((packet.get("diversity") or {}).get("diversified")),
            "research_decision":(packet.get("summary") or {}).get("decision"),
        }
