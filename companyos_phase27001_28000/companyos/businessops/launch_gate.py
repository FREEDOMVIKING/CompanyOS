class LaunchGate:
    def evaluate(self, venture, build_result, finance_result):
        checks = {
            "venture_present": bool(venture),
            "build_success": bool((build_result or {}).get("success")),
            "finance_plan_present": bool(finance_result),
            "treasury_not_blocked": (finance_result or {}).get("status") != "treasury_blocked",
            "production_approval_required": bool(venture.get("requires_launch_approval", True)),
        }
        ready = all([
            checks["venture_present"],
            checks["build_success"],
            checks["finance_plan_present"],
            checks["treasury_not_blocked"],
        ])
        return {
            "ready_for_launch_review": ready,
            "checks": checks,
            "launch_executed": False
        }
