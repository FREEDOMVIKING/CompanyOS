from __future__ import annotations

class VerificationPolicy:
    """265: enforce promotion only after targeted and full regression success."""

    def evaluate(self, result):
        if not result.get("success"):
            return {"approved": False, "reason": "build_failed"}

        regression = result.get("regression", {})
        if not regression.get("success"):
            return {"approved": False, "reason": "regression_failed"}

        registered = result.get("registered", {})
        if not registered or not registered.get("verified"):
            return {"approved": False, "reason": "capability_not_verified"}

        return {"approved": True, "reason": "verified_internal_improvement"}
