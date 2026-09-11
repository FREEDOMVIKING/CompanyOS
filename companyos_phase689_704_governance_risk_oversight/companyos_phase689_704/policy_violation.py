class PolicyViolation:
    """700: detect boundary-crossing attempts."""

    def detect(self, preflight, rollback=None, safe_mode=None):
        reasons=[]
        if preflight.get("approval",{}).get("approval_required"):
            reasons.append("approval_required")
        if not preflight.get("budget",{}).get("within_budget",True):
            reasons.append("budget_exceeded")
        if rollback and not rollback.get("rollback_ready",True):
            reasons.append("rollback_not_ready")
        if safe_mode and safe_mode.get("enabled"):
            reasons.append("safe_mode_enabled")
        return {"violation":bool(reasons),"reasons":reasons}
