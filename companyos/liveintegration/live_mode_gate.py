class LiveModeGate:
    GATED={"send_external_message","production_deploy","bank_transfer","contract_signature",
           "large_marketing_spend","public_campaign_launch","legal_filing","borrow_money",
           "hire_employee","delete_external_resource"}

    def evaluate(self, action, preflight, approval=False):
        gated=action.get("kind") in self.GATED
        allowed=bool(preflight.get("passed")) and (not gated or bool(approval))
        return {
            "allowed":allowed,
            "requires_approval":gated,
            "reason":"ready" if allowed else ("approval_required" if gated and not approval else "preflight_failed")
        }
