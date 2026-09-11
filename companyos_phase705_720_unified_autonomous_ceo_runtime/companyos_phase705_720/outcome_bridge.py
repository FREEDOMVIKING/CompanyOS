from companyos_phase609_624 import DeliveryFeedback

class OutcomeBridge:
    """710: normalize execution/product outcomes for lifecycle ingestion."""

    def normalize(self, result):
        data = (result or {}).get("data") or {}
        payload = data.get("outcome") or result.get("outcome") or {}
        if payload:
            return DeliveryFeedback().build(payload)
        return {
            "mission_success": bool(result.get("success")),
            "tests_passed": bool(data.get("tests_passed", False)),
            "release_candidate_ready": bool(data.get("release_candidate_ready", False)),
            "activation_rate": float(data.get("activation_rate", 0)),
            "retention_rate": float(data.get("retention_rate", 0)),
            "revenue_signal": float(data.get("revenue_signal", 0)),
            "critical_issues": int(data.get("critical_issues", 0)),
        }
