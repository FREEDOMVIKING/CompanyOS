class DualControlPolicy:
    HIGH_IMPACT={"bank_transfer","contract_signature","legal_filing","acquisition","equity_issuance"}
    def evaluate(self, action, approvals):
        required=2 if action.get("kind") in self.HIGH_IMPACT else 1
        count=len(approvals or [])
        return {"required_approvals":required,"approval_count":count,"satisfied":count>=required}
