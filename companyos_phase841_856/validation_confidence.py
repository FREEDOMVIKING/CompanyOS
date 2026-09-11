class ValidationConfidence:
    """850: combine research, problem, pricing, alternatives, and contradiction signals."""
    def score(self, research_confidence, problem_score, pricing_score, contradiction_penalty, false_positive_passed):
        score = (
            float(research_confidence)*0.35
            + float(problem_score)*0.30
            + float(pricing_score)*0.20
            + (1.0-float(contradiction_penalty))*0.15
        )
        if not false_positive_passed:
            score *= 0.7
        return round(max(0.0,min(1.0,score)),3)
