class CapabilityPolicy:
    APPROVAL_GATED={
        "send_external_message",
        "production_deploy",
        "bank_transfer",
        "contract_signature",
        "large_purchase",
        "public_launch"
    }

    def evaluate(self, action_kind, approval=False):
        requires=action_kind in self.APPROVAL_GATED
        return {
            "requires_approval":requires,
            "allowed": (not requires) or bool(approval)
        }
