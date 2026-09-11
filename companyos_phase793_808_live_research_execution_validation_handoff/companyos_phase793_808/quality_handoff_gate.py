class QualityHandoffGate:
    """796: decide whether research can hand off to validation."""

    def evaluate(self, multi_provider_result):
        lifecycle = dict((multi_provider_result or {}).get("lifecycle_evidence") or {})
        packet = dict((multi_provider_result or {}).get("packet") or {})
        confidence = float(lifecycle.get("research_confidence", packet.get("confidence", 0)) or 0)
        ready = bool(lifecycle.get("validation_candidate_ready"))

        return {
            "passed": ready,
            "confidence": confidence,
            "reason": "validation_candidate_ready" if ready else "insufficient_research_evidence",
        }
