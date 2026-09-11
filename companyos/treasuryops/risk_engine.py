class TreasuryRiskEngine:
    def evaluate(self, *, amount, balance, destination_allowed, daily_spend, daily_loss, policy):
        amount = float(amount or 0)
        balance = float(balance or 0)
        daily_spend = float(daily_spend or 0)
        daily_loss = float(daily_loss or 0)

        checks = {
            "positive_amount": amount > 0,
            "within_single_tx_limit": amount <= policy.autonomous_single_tx_limit,
            "within_daily_limit": (daily_spend + amount) <= policy.autonomous_daily_limit,
            "reserve_floor_preserved": (balance - amount) >= policy.reserve_floor,
            "daily_loss_within_limit": daily_loss <= policy.max_daily_loss,
            "destination_allowed": (destination_allowed or not policy.require_allowlist),
            "autonomous_transfers_enabled": bool(policy.allow_autonomous_transfers),
        }

        hard_block = not all([
            checks["positive_amount"],
            checks["within_daily_limit"],
            checks["reserve_floor_preserved"],
            checks["daily_loss_within_limit"],
            checks["destination_allowed"],
        ])

        approval_required = (
            amount > policy.autonomous_single_tx_limit
            or not policy.allow_autonomous_transfers
        )

        return {
            "allowed": (not hard_block) and (not approval_required),
            "approval_required": approval_required and not hard_block,
            "hard_block": hard_block,
            "checks": checks
        }
