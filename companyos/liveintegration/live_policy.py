import os

class LiveExecutionPolicy:
    def __init__(self):
        self.enabled = os.getenv("COMPANYOS_ENABLE_LIVE_FINANCIAL_EXECUTION","").strip().lower() in {"1","true","yes","on"}
        self.max_single = float(os.getenv("COMPANYOS_LIVE_MAX_SINGLE","0.001"))
        self.max_daily = float(os.getenv("COMPANYOS_LIVE_MAX_DAILY","0.005"))
        self.min_reserve = float(os.getenv("COMPANYOS_LIVE_MIN_RESERVE","0.01"))
        self.require_allowlist = os.getenv("COMPANYOS_LIVE_REQUIRE_ALLOWLIST","true").strip().lower() not in {"0","false","no","off"}

        # Compatibility with TreasuryRiskEngine / TreasuryPolicy interface.
        # These aliases preserve the bounded live-policy limits rather than
        # introducing separate or looser financial thresholds.
        self.autonomous_single_tx_limit = self.max_single
        self.autonomous_daily_limit = self.max_daily
        self.reserve_floor = self.min_reserve
        self.max_daily_spend = self.max_daily
        self.max_daily_loss = float(
            os.getenv("COMPANYOS_LIVE_MAX_DAILY_LOSS", str(self.max_daily))
        )

        # Autonomous transfers remain fail-closed unless BOTH the final live
        # financial mode and the autonomous-transfer control are explicitly on.
        self.allow_autonomous_transfers = (
            self.enabled
            and os.getenv(
                "COMPANYOS_AUTONOMOUS_TRANSFERS_ENABLED",
                "false"
            ).strip().lower() in {"1","true","yes","on"}
        )

    def snapshot(self):
        return {
            "live_enabled": self.enabled,
            "max_single": self.max_single,
            "max_daily": self.max_daily,
            "min_reserve": self.min_reserve,
            "require_allowlist": self.require_allowlist
        }

    def check_amount(self, amount):
        amount=float(amount)
        if amount <= 0:
            return {"allowed":False,"status":"invalid_amount"}
        if amount > self.max_single:
            return {"allowed":False,"status":"live_single_limit_exceeded","limit":self.max_single}
        return {"allowed":True,"status":"live_amount_policy_passed"}
