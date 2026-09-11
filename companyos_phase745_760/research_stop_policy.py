class ResearchStopPolicy:
    """755: stop when evidence is sufficient or retry budget exhausted."""
    def decide(self, completeness, confidence, attempts, max_attempts=5):
        if completeness.get("complete") and float(confidence) >= 0.7:
            return {"stop":True,"reason":"sufficient_evidence"}
        if int(attempts) >= int(max_attempts):
            return {"stop":True,"reason":"retry_budget_exhausted"}
        return {"stop":False,"reason":"continue_research"}
