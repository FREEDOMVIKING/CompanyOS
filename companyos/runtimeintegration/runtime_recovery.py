class RuntimeRecoveryManager:
    def classify_cycle(self, cycle_result):
        results = (cycle_result or {}).get("results", [])
        failed = [r for r in results if not r.get("success") and r.get("status") not in {"approval_required","capability_missing"}]
        approvals = [r for r in results if r.get("status") == "approval_required"]
        missing = [r for r in results if r.get("status") == "capability_missing"]

        if failed:
            action = "recover_failed_execution"
        elif missing:
            action = "discover_or_build_missing_capabilities"
        elif approvals:
            action = "wait_for_approval_then_resume"
        else:
            action = "continue_next_cycle"

        return {
            "failed_count": len(failed),
            "approval_required_count": len(approvals),
            "capability_missing_count": len(missing),
            "next_action": action,
        }
