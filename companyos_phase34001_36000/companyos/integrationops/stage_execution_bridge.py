from companyos.capabilityops import StageCapabilityRouter, ControlledAutonomyPolicy
from companyos.executionops import RealCapabilityExecutor

class StageExecutionBridge:
    def __init__(self, root, available_capabilities=None):
        self.root = root
        self.router = StageCapabilityRouter()
        self.policy = ControlledAutonomyPolicy()
        self.executor = RealCapabilityExecutor(root)
        self.available_capabilities = set(available_capabilities or [])

    def execute_stage(self, stage, payload=None, treasury_policy_satisfied=False):
        payload = payload or {}
        route = self.router.resolve(stage, self.available_capabilities)

        action = {
            "stage": stage,
            "impact": payload.get("impact", "medium"),
            "reversible": payload.get("reversible", stage != "launch_review"),
            "moves_money": payload.get("moves_money", stage == "budget"),
            "within_treasury_policy": treasury_policy_satisfied,
            "changes_credentials": payload.get("changes_credentials", False),
            "deploys_production": payload.get("deploys_production", stage == "launch_review"),
        }
        governance = self.policy.decide(action)

        if not route["matched"]:
            return {
                "success": False,
                "stage": stage,
                "status": "capability_missing",
                "route": route,
                "governance": governance,
            }

        if governance["decision"] != "autonomous_allowed":
            return {
                "success": False,
                "stage": stage,
                "status": governance["decision"],
                "route": route,
                "governance": governance,
            }

        execution_payload = {
            "stage": stage,
            "task": payload.get("task") or payload.get("instruction") or f"Execute CompanyOS stage: {stage}",
            "context": payload.get("context", {}),
            "requirements": payload.get("requirements", []),
        }
        execution = self.executor.execute(route["capability"], execution_payload)

        return {
            "success": bool(execution.get("success")),
            "stage": stage,
            "status": execution.get("status"),
            "route": route,
            "governance": governance,
            "execution": execution,
        }
