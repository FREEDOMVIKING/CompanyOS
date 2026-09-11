from __future__ import annotations
from dataclasses import asdict
from companyos.runtime.portfolio_manager import PortfolioManager
from companyos.runtime.recovery_manager import RecoveryManager

def dashboard():
    portfolio=PortfolioManager().summary()
    recovery=RecoveryManager().scan()
    return {
        "portfolio":asdict(portfolio),
        "recovery":asdict(recovery),
        "external_action_execution":False,
        "transaction_broadcast_override":False,
    }
