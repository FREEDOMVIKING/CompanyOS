class ExternalActionApprovalGate:
    HIGH_RISK={
        "send_external_email",
        "publish_public_content",
        "production_deploy",
        "bank_transfer",
        "contract_signature",
        "large_marketing_spend",
        "create_external_account",
        "delete_external_resource",
    }

    def evaluate(self, action, amount=0, autonomous_limit=250):
        kind=action.get("kind") if isinstance(action,dict) else str(action)
        amount=float(amount or (action.get("amount",0) if isinstance(action,dict) else 0) or 0)
        gated=kind in self.HIGH_RISK or amount>float(autonomous_limit)
        return {
            "kind":kind,
            "amount":amount,
            "requires_approval":gated,
            "allowed":not gated,
            "reason":"explicit_approval_required" if gated else "within_delegated_authority"
        }
