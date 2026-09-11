class AdaptiveRoundDecision:
    """929: decide build, continue, review, or archive after adaptive validation."""
    def decide(self, validation, improvement, novelty, strategy_attempt, max_strategy_attempts=3):
        decision=validation.get("decision")
        confidence=float((validation.get("scores") or {}).get("validation_confidence",0))
        if decision=="GO":
            return {"decision":"GO","action":"build"}
        if decision=="KILL":
            return {"decision":"KILL","action":"archive"}
        if int(strategy_attempt)>=int(max_strategy_attempts):
            return {"decision":"HUMAN_REVIEW" if confidence>=0.45 else "KILL",
                    "action":"review" if confidence>=0.45 else "archive"}
        if not improvement.get("improved") and float(novelty)<0.25:
            return {"decision":"HUMAN_REVIEW","action":"review"}
        return {"decision":"REVISE","action":"continue_adaptive_research"}
