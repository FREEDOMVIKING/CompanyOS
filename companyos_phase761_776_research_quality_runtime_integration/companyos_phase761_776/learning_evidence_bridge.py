class LearningEvidenceBridge:
    """769: expose research quality to strategic learning context."""
    def build(self,quality):
        packet=quality.get("packet") or {}
        return {
            "evidence_confidence":packet.get("confidence",0),
            "evidence_complete":(packet.get("completeness") or {}).get("complete",False),
            "source_diversified":(packet.get("diversity") or {}).get("diversified",False),
            "contradiction_topics":(packet.get("contradictions") or {}).get("topics",[]),
        }
