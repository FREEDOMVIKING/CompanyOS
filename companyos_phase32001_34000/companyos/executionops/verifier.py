class ExecutionVerifier:
    def verify(self, result):
        result = result or {}
        success = bool(result.get("success"))
        evidence = any([
            result.get("receipt"),
            result.get("tx_id"),
            result.get("artifact"),
            result.get("path"),
            result.get("output"),
            result.get("status") in {"complete","completed","success","executed"},
        ])
        return {
            "passed": bool(success and evidence),
            "success_flag": success,
            "evidence_present": bool(evidence),
        }
