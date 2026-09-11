class OutcomeIngestor:
    """580: normalize measured execution/market outcomes."""

    def ingest(self, payload):
        payload = dict(payload or {})
        return {
            "mission_success": bool(payload.get("mission_success")),
            "tests_passed": bool(payload.get("tests_passed")),
            "release_candidate_ready": bool(payload.get("release_candidate_ready")),
            "activation_rate": float(payload.get("activation_rate", 0)),
            "retention_rate": float(payload.get("retention_rate", 0)),
            "revenue_signal": float(payload.get("revenue_signal", 0)),
            "critical_issues": int(payload.get("critical_issues", 0)),
            "notes": payload.get("notes"),
        }
