class QualityGates:
    """409: release quality contract."""

    def gates(self):
        return [
            "targeted_tests_pass",
            "regression_tests_pass",
            "no_known_critical_defects",
            "core_workflow_verified",
            "telemetry_verified",
            "secrets_not_committed",
            "rollback_plan_present",
        ]
