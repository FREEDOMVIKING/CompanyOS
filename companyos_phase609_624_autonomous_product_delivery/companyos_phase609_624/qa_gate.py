class QAGate:
    """615: QA gate before release candidate promotion."""

    def evaluate(self, evidence):
        required = [
            "targeted_tests_pass",
            "regression_tests_pass",
            "no_known_critical_defects",
            "core_workflow_verified",
            "telemetry_verified",
        ]
        passed = {k: bool(evidence.get(k)) for k in required}
        return {
            "passed": all(passed.values()),
            "checks": passed,
            "missing": [k for k,v in passed.items() if not v],
        }
