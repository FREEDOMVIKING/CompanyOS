from __future__ import annotations

class CapabilityMapper:
    """263: map an improvement into a concrete self-build capability."""

    MAP = {
        "test_infrastructure": "self_test_scaffold",
        "capability_registry_hardening": "capability_registry_diagnostics",
        "provider_activation_observability": "provider_activation_diagnostics",
        "runtime_health_diagnostics": "runtime_health_diagnostics",
    }

    def map(self, improvement):
        name = improvement.get("improvement", "runtime_health_diagnostics")
        capability = self.MAP.get(name, name)
        return {
            "capability": capability,
            "module_name": f"generated_{capability}",
            "priority": improvement.get("priority", .5),
            "reason": improvement.get("reason"),
        }
