class ComplianceGate:
    """122: require review for regulated/high-impact categories."""
    REVIEW={"financial_transaction","legal_commitment","regulated_data","employment_action","public_claim"}
    def evaluate(self,action):
        category=str(action.get("category",""))
        required=category in self.REVIEW or bool(action.get("compliance_review_required",False))
        reviewed=bool(action.get("compliance_reviewed",False))
        return {"review_required":required,"allowed":(not required) or reviewed,"category":category}
