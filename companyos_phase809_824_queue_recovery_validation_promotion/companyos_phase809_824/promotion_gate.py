class PromotionGate:
    """816: determine whether recovered research qualifies for validation."""

    def evaluate(self, recovery_result):
        cycle = dict((recovery_result or {}).get("research_cycle") or {})
        gate = dict(cycle.get("gate") or {})
        return {
            "promote": bool(gate.get("passed")),
            "confidence": float(gate.get("confidence",0) or 0),
            "reason": gate.get("reason"),
        }
