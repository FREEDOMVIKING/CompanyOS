class ReleasePlan:
    """410: reversible release preparation."""

    def build(self):
        return {
            "stages":["internal","limited_beta","measured_release"],
            "requires":["quality_gate_pass","telemetry","rollback_plan"],
            "automatic_irreversible_external_launch": False,
            "rollback_required": True,
        }
