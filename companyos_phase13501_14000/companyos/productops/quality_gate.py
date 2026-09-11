class ProductQualityGate:
    def evaluate(self, signals):
        checks={
            "tests":bool(signals.get("tests_passed",False)),
            "security":bool(signals.get("security_passed",False)),
            "performance":bool(signals.get("performance_passed",False)),
            "rollback":bool(signals.get("rollback_ready",False)),
            "observability":bool(signals.get("observability_ready",False))
        }
        return {"passed":all(checks.values()),"checks":checks}
