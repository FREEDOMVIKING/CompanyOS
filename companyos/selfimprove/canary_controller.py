class CanaryController:
    def decide(self, sandbox_result, regression_result, exposure=.1):
        allowed=bool(sandbox_result.get("safe_for_canary")) and bool(regression_result.get("passed"))
        return {
            "allowed":allowed,
            "exposure":float(exposure) if allowed else 0.0,
            "action":"run_canary" if allowed else "hold"
        }
