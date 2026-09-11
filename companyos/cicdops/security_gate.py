class SecurityGate:
    def evaluate(self, scans):
        result = {
            "security_scan": bool(scans.get("security_scan", False)),
            "dependency_scan": bool(scans.get("dependency_scan", False)),
            "secrets_scan": bool(scans.get("secrets_scan", False)),
        }
        return {"passed": all(result.values()), "checks": result}
