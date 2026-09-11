from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from companyos.walletintegration.live_treasury_feed import LiveTreasuryFeed, TreasurySnapshot


@dataclass(frozen=True)
class TreasuryAuthorizationDecision:
    allowed: bool
    reason: str
    requested_sol: float
    current_balance_sol: float
    reserve_sol: float
    spendable_sol: float
    rpc_ok: bool
    stale: bool


class LiveTreasuryAuthorizer:
    """
    Financial authorization based on a forced-fresh treasury snapshot.

    This module does NOT create, sign, or broadcast transactions.
    It only decides whether a requested SOL amount is financially admissible
    against the latest live balance and configured reserve.
    """

    def __init__(self, feed: LiveTreasuryFeed) -> None:
        self.feed = feed

    def authorize_sol(self, requested_sol: float) -> TreasuryAuthorizationDecision:
        requested = float(requested_sol)

        if requested < 0:
            return TreasuryAuthorizationDecision(
                allowed=False,
                reason="negative_amount_rejected",
                requested_sol=requested,
                current_balance_sol=0.0,
                reserve_sol=self.feed.reserve_sol,
                spendable_sol=0.0,
                rpc_ok=False,
                stale=True,
            )

        try:
            snap = self.feed.force_fresh_before_financial_action()
        except Exception:
            return TreasuryAuthorizationDecision(
                allowed=False,
                reason="fresh_treasury_state_unavailable",
                requested_sol=requested,
                current_balance_sol=0.0,
                reserve_sol=self.feed.reserve_sol,
                spendable_sol=0.0,
                rpc_ok=False,
                stale=True,
            )

        if requested > snap.spendable_sol:
            return TreasuryAuthorizationDecision(
                allowed=False,
                reason="insufficient_spendable_balance_after_reserve",
                requested_sol=requested,
                current_balance_sol=snap.sol_balance,
                reserve_sol=snap.reserve_sol,
                spendable_sol=snap.spendable_sol,
                rpc_ok=snap.rpc_ok,
                stale=snap.stale,
            )

        return TreasuryAuthorizationDecision(
            allowed=True,
            reason="fresh_balance_authorized",
            requested_sol=requested,
            current_balance_sol=snap.sol_balance,
            reserve_sol=snap.reserve_sol,
            spendable_sol=snap.spendable_sol,
            rpc_ok=snap.rpc_ok,
            stale=snap.stale,
        )
