from companyos_phase689_704 import PreflightCheck, RollbackPolicy, PolicyViolation, SafeMode

class GovernedActionRouter:
    """708: enforce governance before any routed action."""

    def __init__(self, root):
        self.safe_mode = SafeMode(root)

    def route(self, action, limits=None):
        preflight = PreflightCheck().run(action, limits)
        rollback = RollbackPolicy().evaluate(action)
        safe = self.safe_mode.status()
        violation = PolicyViolation().detect(preflight, rollback, safe)

        return {
            "allowed": bool(preflight.get("allowed_to_execute")) and not violation.get("violation"),
            "preflight": preflight,
            "rollback": rollback,
            "safe_mode": safe,
            "violation": violation,
        }
