class LifecycleEvidenceBridge:
    """768: convert research quality packet to lifecycle evidence flags."""
    def build(self,quality):
        packet=quality.get("packet") or {}
        summary=quality.get("summary") or {}
        return {
            "validation_candidate_ready":bool(quality.get("passed")),
            "research_confidence":float(packet.get("confidence",0)),
            "research_complete":bool((packet.get("completeness") or {}).get("complete")),
            "research_contradictions":len((packet.get("contradictions") or {}).get("topics",[])),
            "research_decision":summary.get("decision"),
        }
