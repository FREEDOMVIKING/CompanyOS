from __future__ import annotations

class HandoffReadiness:
    """243: determine whether CompanyOS can begin proposing/building its own roadmap."""

    REQUIRED = [
        "phase220_self_build_pipeline",
        "phase228_real_coder_loop",
        "provider_probe_passed",
        "first_real_model_build_passed",
        "full_regression_passed",
        "rollback_available",
        "persistent_runtime",
    ]

    def evaluate(self, signals):
        missing = [x for x in self.REQUIRED if not bool(signals.get(x))]
        return {
            "ready": not missing,
            "missing": missing,
            "autonomous_roadmap_handoff": not missing,
        }
