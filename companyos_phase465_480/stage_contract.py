class StageContract:
    """465: canonical stage result contract for the unified CEO loop."""

    REQUIRED = ("success","status","stage")

    def normalize(self, result, stage):
        result = dict(result or {})
        result.setdefault("success", False)
        result.setdefault("status", "unknown")
        result.setdefault("stage", stage)
        result.setdefault("data", {})
        return result
