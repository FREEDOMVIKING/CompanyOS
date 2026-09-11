from .policy import TreasuryPolicy

class TreasuryStatus:
    def status(self):
        p = TreasuryPolicy.from_env()
        return {
            "success": True,
            "status": "phase22000_autonomous_treasury_safety_kernel_ready",
            "policy": p.to_dict(),
            "safe_default": not p.allow_autonomous_transfers,
            "execution_connector_required_for_real_money": True,
            "allowlist_support": True,
            "reserve_floor": True,
            "daily_limit": True,
            "single_tx_limit": True,
            "daily_loss_limit": True,
            "ledger": True,
            "reconciliation": True
        }
