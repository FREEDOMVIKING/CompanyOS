class ValidationEngine:
    """200: evidence gates for autonomous iteration without blocking routine work."""
    def evaluate(self, evidence):
        samples=int(evidence.get("samples",0)); confidence=float(evidence.get("confidence",0)); score=float(evidence.get("score",0))
        strong=samples>=3 and confidence>=.65 and score>=.55
        return {"validated":strong,"next_action":"advance" if strong else "collect_more_evidence",
                "autonomous_next_action":True}
