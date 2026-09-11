class LearningLoop:
    """460: turn measured outcomes into explicit learning records."""

    def record(self, hypothesis, result, metric_delta):
        return {
            "hypothesis":hypothesis,
            "result":result,
            "metric_delta":metric_delta,
            "learning":"keep" if metric_delta > 0 else "revise_or_reject",
        }
