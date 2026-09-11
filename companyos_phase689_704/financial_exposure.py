class FinancialExposure:
    """693: financial exposure classification and hard gates."""

    def evaluate(self, action):
        amount = float(action.get("financial_commitment_usd",0))
        if amount <= 0:
            level = "none"
        elif amount <= 50:
            level = "low"
        elif amount <= 500:
            level = "medium"
        else:
            level = "high"
        return {
            "exposure_level": level,
            "amount_usd": amount,
            "automatic_transfer_authorized": False,
            "automatic_purchase_authorized": False,
        }
