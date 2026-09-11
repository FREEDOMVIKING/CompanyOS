class RealCapabilityOperatingExecutor:
    def __init__(self, router, policy):
        self.router = router
        self.policy = policy

    def build_stage_plan(self, stages, available_capabilities, treasury_policy_satisfied=False):
        rows = []
        for stage in stages:
            route = self.router.resolve(stage, available_capabilities)
            action = {
                "stage": stage,
                "impact": "medium" if stage in {"build","test","operate","customers","revenue","accounting"} else "low",
                "reversible": stage not in {"launch_review"},
                "moves_money": stage == "budget",
                "within_treasury_policy": treasury_policy_satisfied,
                "changes_credentials": False,
                "deploys_production": stage == "launch_review",
            }
            governance = self.policy.decide(action)

            if not route["matched"]:
                execution_state = "capability_missing"
            elif governance["decision"] == "autonomous_allowed":
                execution_state = "ready_to_execute_real_capability"
            else:
                execution_state = governance["decision"]

            rows.append({
                "stage": stage,
                "route": route,
                "governance": governance,
                "execution_state": execution_state,
            })
        return rows
