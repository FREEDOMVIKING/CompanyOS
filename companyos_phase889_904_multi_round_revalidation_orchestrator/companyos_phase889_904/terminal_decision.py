class TerminalDecisionResolver:
    """893: resolve GO/KILL/HUMAN_REVIEW/EXHAUSTED."""
    def resolve(self,validation,convergence,diminishing,round_no,max_rounds=3):
        decision=validation.get("decision")
        confidence=float((validation.get("scores") or {}).get("validation_confidence",0))
        if decision=="GO": return {"decision":"GO","action":"build"}
        if decision=="KILL": return {"decision":"KILL","action":"archive"}
        if convergence.get("decision")=="STALLED_REVISE" or diminishing.get("diminishing"):
            return {"decision":"HUMAN_REVIEW","action":"review"}
        if int(round_no)>=int(max_rounds):
            return {"decision":"EXHAUSTED","action":"archive" if confidence<0.45 else "review"}
        return {"decision":"REVISE","action":"continue"}
