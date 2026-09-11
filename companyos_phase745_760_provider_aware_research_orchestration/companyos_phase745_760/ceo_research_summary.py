class CEOResearchSummary:
    """759: concise decision-oriented research summary."""
    def build(self, packet):
        return {
            "evidence_count":len(packet.get("evidence",[])),
            "confidence":packet.get("confidence",0),
            "complete":packet.get("completeness",{}).get("complete",False),
            "contradictions":packet.get("contradictions",{}).get("topics",[]),
            "provider":(packet.get("provider") or {}).get("name"),
            "decision":"advance_to_validation" if packet.get("confidence",0) >= 0.7 and packet.get("completeness",{}).get("complete") else "continue_research",
        }
