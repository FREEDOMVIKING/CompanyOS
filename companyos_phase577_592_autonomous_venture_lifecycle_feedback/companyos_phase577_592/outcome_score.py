class OutcomeScore:
    """584: score whether the latest venture cycle produced meaningful progress."""

    def score(self, before_stage, after_stage, evidence):
        score = 0.0
        if before_stage != after_stage:
            score += 4.0
        if evidence.get("mission_success"):
            score += 1.5
        if evidence.get("tests_passed"):
            score += 1.5
        score += min(1.5, float(evidence.get("activation_rate",0))*3)
        score += min(1.5, float(evidence.get("retention_rate",0))*3)
        return round(min(10.0, score), 2)
