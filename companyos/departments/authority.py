class AuthorityGate:
    HUMAN_APPROVAL = {"contract_signature","large_marketing_spend","bank_transfer",
                      "external_account_creation","legal_filing","production_delete"}

    def evaluate(self, action):
        kind = action.get("kind","")
        amount = float(action.get("amount",0) or 0)
        gated = kind in self.HUMAN_APPROVAL or amount >= 500
        return {
            "allowed": not gated,
            "requires_approval": gated,
            "reason": "human_approval_required" if gated else "within_delegated_authority"
        }
