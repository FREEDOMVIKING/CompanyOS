from __future__ import annotations

class MissionSeed:
    """240: create a first genuine, low-risk self-build mission."""

    def create(self):
        return {
            "goal": "add_verified_internal_health_summary_capability",
            "required_capabilities": ["internal_health_summary"],
            "priority": 1.0,
            "constraints": [
                "internal_only",
                "no_external_actions",
                "no_financial_actions",
                "must_include_tests",
                "must_pass_full_regression_suite",
            ],
        }
