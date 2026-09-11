class IntegratedOperatingCycleExecutor:
    STAGES = [
        "discover","research","select","plan","budget","build","test",
        "launch_review","operate","customers","revenue","accounting",
        "evaluate","portfolio_decision","learn"
    ]

    def __init__(self, bridge):
        self.bridge = bridge

    def run(self, stage_payloads=None, treasury_policy_satisfied=False):
        stage_payloads = stage_payloads or {}
        results = []
        for stage in self.STAGES:
            result = self.bridge.execute_stage(
                stage,
                payload=stage_payloads.get(stage, {}),
                treasury_policy_satisfied=treasury_policy_satisfied
            )
            results.append(result)

            if result.get("status") == "blocked":
                break

        verified = sum(1 for r in results if r.get("success"))
        approvals = sum(1 for r in results if r.get("status") == "approval_required")
        missing = sum(1 for r in results if r.get("status") == "capability_missing")

        return {
            "success": all(
                r.get("success") or r.get("status") in {"approval_required","capability_missing"}
                for r in results
            ),
            "results": results,
            "verified_stage_count": verified,
            "approval_required_count": approvals,
            "capability_missing_count": missing,
            "next_action": (
                "continue_or_repeat_cycle"
                if approvals == 0 and missing == 0
                else "resolve_gates_or_missing_capabilities"
            )
        }
