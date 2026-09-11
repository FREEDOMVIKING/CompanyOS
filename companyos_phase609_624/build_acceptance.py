class BuildAcceptance:
    """614: distinguish code generation from a usable build."""

    def evaluate(self, result):
        checks = {
            "artifacts_present": bool(result.get("artifacts")),
            "core_workflow_verified": bool(result.get("core_workflow_verified")),
            "tests_passed": bool(result.get("tests_passed")),
            "documentation_present": bool(result.get("documentation_present")),
        }
        return {
            "accepted": all(checks.values()),
            "checks": checks,
            "missing": [k for k,v in checks.items() if not v],
        }
