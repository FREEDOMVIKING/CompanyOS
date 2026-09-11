class CIQualityGate:
    def evaluate(self, checks):
        required = ["lint","static_analysis","unit_tests","integration_tests"]
        result = {k: bool(checks.get(k, False)) for k in required}
        return {"passed": all(result.values()), "checks": result}
