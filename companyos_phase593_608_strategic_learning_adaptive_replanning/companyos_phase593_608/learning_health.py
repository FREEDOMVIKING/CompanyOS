class LearningHealth:
    """607: sanity checks for strategic learning outputs."""

    def evaluate(self, result):
        return {
            "healthy": bool(result.get("lessons")) and bool(result.get("rewritten_mission")),
            "lesson_count": len(result.get("lessons",[])),
            "has_strategy": bool(result.get("strategy")),
            "confidence": result.get("confidence"),
        }
