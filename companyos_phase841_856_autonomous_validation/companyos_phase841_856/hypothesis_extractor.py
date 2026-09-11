class HypothesisExtractor:
    """842: extract testable hypotheses from research evidence."""
    def extract(self, adapted):
        packet = dict((adapted or {}).get("research_packet") or {})
        summary = dict(packet.get("summary") or {})
        evidence = list(packet.get("evidence") or [])
        hypotheses = []
        hypotheses.append({
            "type":"problem",
            "statement":"Target users experience a meaningful recurring problem.",
            "supporting_evidence":len(evidence),
        })
        hypotheses.append({
            "type":"demand",
            "statement":"Target users show measurable demand for a solution.",
            "supporting_evidence":len([e for e in evidence if "demand" in e.get("tags",[])]),
        })
        hypotheses.append({
            "type":"pricing",
            "statement":"Target users have willingness to pay at a viable price.",
            "supporting_evidence":len([e for e in evidence if "pricing" in e.get("tags",[])]),
        })
        return {"hypotheses": hypotheses, "research_decision": summary.get("decision")}
