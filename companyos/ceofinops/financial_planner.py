class FinancialPlanner:
    def build_plan(self, opportunity):
        opportunity = opportunity or {}
        required = float(opportunity.get("required_capital", opportunity.get("budget", 0)) or 0)
        expected_return = float(opportunity.get("expected_return", 0) or 0)
        confidence = float(opportunity.get("confidence", 0.5) or 0.5)
        risk = float(opportunity.get("risk", 0.5) or 0.5)
        horizon_days = int(opportunity.get("horizon_days", 30) or 30)

        return {
            "name": opportunity.get("name") or opportunity.get("title") or "Unnamed opportunity",
            "required_capital": required,
            "expected_return": expected_return,
            "confidence": confidence,
            "risk": risk,
            "horizon_days": horizon_days,
            "destination": opportunity.get("destination"),
            "chain": opportunity.get("chain", "solana"),
            "source": opportunity.get("source"),
            "purpose": opportunity.get("purpose") or opportunity.get("description") or "CompanyOS autonomous financial plan",
            "token_mint": opportunity.get("token_mint"),
            "token_contract": opportunity.get("token_contract"),
        }
