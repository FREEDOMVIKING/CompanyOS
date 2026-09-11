from dataclasses import dataclass, asdict
import os

@dataclass
class TreasuryPolicy:
    autonomous_single_tx_limit: float = 25.0
    autonomous_daily_limit: float = 100.0
    reserve_floor: float = 250.0
    max_daily_loss: float = 50.0
    require_allowlist: bool = True
    allow_autonomous_transfers: bool = False
    approval_above_single_tx_limit: bool = True

    @classmethod
    def from_env(cls):
        def f(name, default):
            try:
                return float(os.getenv(name, str(default)))
            except Exception:
                return float(default)

        def b(name, default):
            raw = os.getenv(name)
            if raw is None:
                return bool(default)
            return raw.strip().lower() in {"1","true","yes","on"}

        return cls(
            autonomous_single_tx_limit=f("COMPANYOS_AUTONOMOUS_SINGLE_TX_LIMIT", 25.0),
            autonomous_daily_limit=f("COMPANYOS_AUTONOMOUS_DAILY_LIMIT", 100.0),
            reserve_floor=f("COMPANYOS_TREASURY_RESERVE_FLOOR", 250.0),
            max_daily_loss=f("COMPANYOS_MAX_DAILY_LOSS", 50.0),
            require_allowlist=b("COMPANYOS_REQUIRE_DESTINATION_ALLOWLIST", True),
            allow_autonomous_transfers=b("COMPANYOS_ALLOW_AUTONOMOUS_TRANSFERS", False),
            approval_above_single_tx_limit=b("COMPANYOS_APPROVAL_ABOVE_SINGLE_TX_LIMIT", True),
        )

    def to_dict(self):
        return asdict(self)
