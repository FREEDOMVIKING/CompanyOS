from __future__ import annotations

class ImprovementPlanner:
    """262: choose a bounded internal improvement from observed gaps."""

    def propose(self, observation):
        s = observation.get("signals", {})

        if not s.get("tests_dir_exists"):
            return {
                "improvement": "test_infrastructure",
                "priority": 1.0,
                "reason": "tests_directory_missing",
                "internal_only": True,
            }

        if not s.get("capability_registry_exists"):
            return {
                "improvement": "capability_registry_hardening",
                "priority": .9,
                "reason": "capability_registry_missing",
                "internal_only": True,
            }

        if not s.get("provider_activation_exists"):
            return {
                "improvement": "provider_activation_observability",
                "priority": .8,
                "reason": "provider_activation_state_missing",
                "internal_only": True,
            }

        return {
            "improvement": "runtime_health_diagnostics",
            "priority": .6,
            "reason": "baseline_internal_improvement",
            "internal_only": True,
        }
