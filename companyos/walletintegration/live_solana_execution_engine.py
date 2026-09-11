from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Any

from companyos.walletintegration.live_treasury_feed import LiveTreasuryFeed
from companyos.walletintegration.live_treasury_authorizer import LiveTreasuryAuthorizer
from companyos.walletintegration.lifecycle_execution_bridge import LifecycleExecutionBridge
from companyos.walletintegration.solana_rpc_preflight import rpc_call
from companyos.walletintegration.solana_legacy_tx_builder import build_zero_lamport_self_transfer, build_sol_transfer, build_sol_transfer
from companyos.walletintegration.controlled_solana_broadcaster import ControlledSolanaBroadcaster
from companyos.walletintegration.solana_confirmation_tracker import wait_for_signature_status
from companyos.walletintegration.solana_transaction_simulator import simulate_signed_transaction


@dataclass(frozen=True)
class LiveExecutionResult:
    success: bool
    lifecycle_id: str
    state: str
    signature: Optional[str]
    reason: str
    confirmation_status: Optional[str]
    status_err: Any
    balance_before_lamports: int
    balance_after_lamports: Optional[int]
    observed_balance_delta_lamports: Optional[int]


class LiveSolanaExecutionEngine:
    """
    Production execution lifecycle wrapper.

    Current supported live transaction type:
      zero-lamport self-transfer (validation path only)

    The engine:
      fresh balance -> authorize -> lifecycle AUTHORIZED -> build/sign ->
      SIGNED -> optional broadcast -> SUBMITTED -> confirm -> CONFIRMED ->
      reconcile balance -> FINALIZED/FAILED

    Broadcasting is OFF unless explicitly enabled on construction.
    """

    def __init__(
        self,
        *,
        rpc_url: str,
        secret: str,
        encoding: str,
        wallet_address: str,
        reserve_sol: float,
        broadcast_enabled: bool = False,
    ) -> None:
        self.rpc_url = rpc_url
        self.secret = secret
        self.encoding = encoding
        self.wallet_address = wallet_address
        self.feed = LiveTreasuryFeed(
            rpc_url,
            wallet_address,
            reserve_sol=reserve_sol,
            stale_after_seconds=60,
        )
        self.authorizer = LiveTreasuryAuthorizer(self.feed)
        self.lifecycle = LifecycleExecutionBridge()
        self.broadcaster = ControlledSolanaBroadcaster(
            rpc_url,
            broadcast_enabled=broadcast_enabled,
        )

    def _balance_lamports(self) -> int:
        data = rpc_call(
            self.rpc_url,
            "getBalance",
            [self.wallet_address, {"commitment": "confirmed"}],
        )
        return int((data.get("result") or {}).get("value"))

    def execute_zero_self_transfer(
        self,
        *,
        allow_broadcast: bool = False,
        confirm_token: str = "",
        wait_timeout_seconds: float = 60.0,
    ) -> LiveExecutionResult:
        requested_sol = 0.0

        decision = self.authorizer.authorize_sol(requested_sol)
        balance_before = self._balance_lamports()

        ctx = self.lifecycle.begin(
            wallet_address=self.wallet_address,
            destination=self.wallet_address,
            requested_lamports=0,
            balance_before_lamports=balance_before,
            metadata={
                "engine": "LiveSolanaExecutionEngine",
                "transaction_type": "zero_lamport_self_transfer",
                "broadcast_requested": bool(allow_broadcast),
            },
        )

        if not decision.allowed:
            self.lifecycle.mark_failed(
                ctx,
                error=decision.reason,
                balance_after_lamports=balance_before,
            )
            return LiveExecutionResult(
                False, ctx.record.lifecycle_id, ctx.record.state, None,
                decision.reason, None, decision.reason,
                balance_before, balance_before,
                ctx.record.observed_balance_delta_lamports,
            )

        latest = rpc_call(
            self.rpc_url,
            "getLatestBlockhash",
            [{"commitment": "confirmed"}],
        )
        blockhash = ((latest.get("result") or {}).get("value") or {}).get("blockhash")
        if not blockhash:
            self.lifecycle.mark_failed(ctx, error="latest_blockhash_unavailable")
            return LiveExecutionResult(
                False, ctx.record.lifecycle_id, ctx.record.state, None,
                "latest_blockhash_unavailable", None, "latest_blockhash_unavailable",
                balance_before, None, None,
            )

        tx = build_zero_lamport_self_transfer(
            self.secret,
            self.encoding,
            blockhash,
        )
        self.lifecycle.mark_signed(ctx)

        if not allow_broadcast:
            return LiveExecutionResult(
                True, ctx.record.lifecycle_id, ctx.record.state, None,
                "signed_not_broadcast", None, None,
                balance_before, None, None,
            )

        result = self.broadcaster.send_serialized_transaction(
            tx.transaction_base64,
            confirm_token=confirm_token,
            skip_preflight=False,
            preflight_commitment="confirmed",
            max_retries=3,
        )

        if not result.submitted or not result.signature:
            self.lifecycle.mark_failed(
                ctx,
                error=result.error or "broadcast_failed",
            )
            return LiveExecutionResult(
                False, ctx.record.lifecycle_id, ctx.record.state, None,
                result.error or "broadcast_failed", None,
                result.error or "broadcast_failed",
                balance_before, None, None,
            )

        self.lifecycle.mark_submitted(ctx, result.signature)

        confirmation = wait_for_signature_status(
            self.rpc_url,
            result.signature,
            timeout_seconds=wait_timeout_seconds,
            poll_interval_seconds=2.0,
        )

        if not confirmation.confirmed:
            balance_after = self._balance_lamports()
            self.lifecycle.mark_failed(
                ctx,
                error=confirmation.err or "confirmation_timeout",
                confirmation_status=confirmation.confirmation_status,
                slot=confirmation.slot,
                balance_after_lamports=balance_after,
            )
            return LiveExecutionResult(
                False, ctx.record.lifecycle_id, ctx.record.state, result.signature,
                "not_confirmed",
                confirmation.confirmation_status,
                confirmation.err,
                balance_before,
                balance_after,
                ctx.record.observed_balance_delta_lamports,
            )

        self.lifecycle.mark_confirmed(
            ctx,
            confirmation_status=confirmation.confirmation_status or "confirmed",
            slot=confirmation.slot,
            status_err=confirmation.err,
        )

        balance_after = self._balance_lamports()

        # Treat confirmed as landed success; lifecycle finalization is a
        # reconciliation terminal state in this engine even when cluster status
        # is still "confirmed". The exact chain confirmation string is preserved.
        self.lifecycle.mark_finalized(
            ctx,
            confirmation_status=confirmation.confirmation_status or "confirmed",
            slot=confirmation.slot,
            balance_after_lamports=balance_after,
        )

        return LiveExecutionResult(
            True,
            ctx.record.lifecycle_id,
            ctx.record.state,
            result.signature,
            "confirmed_and_reconciled",
            confirmation.confirmation_status,
            confirmation.err,
            balance_before,
            balance_after,
            ctx.record.observed_balance_delta_lamports,
        )

    def execute_sol_transfer(
        self,
        *,
        destination: str,
        amount_lamports: int,
        allow_broadcast: bool = False,
        confirm_token: str = "",
        wait_timeout_seconds: float = 60.0,
    ) -> LiveExecutionResult:
        requested_lamports=int(amount_lamports)
        destination=str(destination or "").strip()

        def response(**kw):
            defaults=dict(
                success=False, lifecycle_id="", state="FAILED", signature=None,
                reason="", confirmation_status=None, status_err=None,
                balance_before_lamports=0, balance_after_lamports=None,
                observed_balance_delta_lamports=None,
            )
            defaults.update(kw)
            return LiveExecutionResult(**defaults)

        if requested_lamports <= 0:
            return response(reason="amount_must_be_positive")
        if not destination:
            return response(reason="destination_required")

        requested_sol=requested_lamports/1_000_000_000
        decision=self.authorizer.authorize_sol(requested_sol)
        balance_before=self._balance_lamports()

        ctx=self.lifecycle.begin(
            wallet_address=self.wallet_address,
            destination=destination,
            requested_lamports=requested_lamports,
            balance_before_lamports=balance_before,
            metadata={
                "engine":"LiveSolanaExecutionEngine",
                "transaction_type":"sol_transfer",
                "broadcast_requested":bool(allow_broadcast),
            },
        )

        if not decision.allowed:
            self.lifecycle.mark_failed(ctx,error=decision.reason,balance_after_lamports=balance_before)
            return response(
                lifecycle_id=ctx.record.lifecycle_id,
                state=ctx.record.state,
                reason=decision.reason,
                balance_before_lamports=balance_before,
                balance_after_lamports=balance_before,
                observed_balance_delta_lamports=0,
            )

        try:
            latest=rpc_call(self.rpc_url,"getLatestBlockhash",[{"commitment":"confirmed"}])
            blockhash=(((latest.get("result") or {}).get("value") or {}).get("blockhash"))
            if not blockhash: raise RuntimeError("latest_blockhash_unavailable")

            tx=build_sol_transfer(self.secret,self.encoding,blockhash,destination,requested_lamports)
            sim=simulate_signed_transaction(self.rpc_url,tx.transaction_base64,commitment="confirmed")
            if not sim.rpc_ok or not sim.simulation_ok:
                err=sim.err or "simulation_failed"
                self.lifecycle.mark_failed(ctx,error=err,balance_after_lamports=balance_before)
                return response(
                    lifecycle_id=ctx.record.lifecycle_id,state=ctx.record.state,reason=err,status_err=err,
                    balance_before_lamports=balance_before,balance_after_lamports=balance_before,
                    observed_balance_delta_lamports=0,
                )

            self.lifecycle.mark_signed(ctx)
            if not allow_broadcast:
                return response(success=True,lifecycle_id=ctx.record.lifecycle_id,state=ctx.record.state,
                                reason="signed_simulated_not_broadcast",balance_before_lamports=balance_before)

            result=self.broadcaster.send_serialized_transaction(
                tx.transaction_base64,confirm_token=confirm_token,skip_preflight=False,
                preflight_commitment="confirmed",max_retries=3,
            )
            if not result.submitted or not result.signature:
                err=result.error or "broadcast_failed"
                self.lifecycle.mark_failed(ctx,error=err)
                return response(lifecycle_id=ctx.record.lifecycle_id,state=ctx.record.state,reason=err,
                                status_err=err,balance_before_lamports=balance_before)

            self.lifecycle.mark_submitted(ctx,result.signature)
            confirmation=wait_for_signature_status(
                self.rpc_url,result.signature,timeout_seconds=wait_timeout_seconds,poll_interval_seconds=2.0,
            )
            if not confirmation.confirmed:
                balance_after=self._balance_lamports()
                err=confirmation.err or "confirmation_timeout"
                self.lifecycle.mark_failed(ctx,error=err,confirmation_status=confirmation.confirmation_status,
                                           slot=confirmation.slot,balance_after_lamports=balance_after)
                return response(
                    lifecycle_id=ctx.record.lifecycle_id,state=ctx.record.state,signature=result.signature,
                    reason="not_confirmed",confirmation_status=confirmation.confirmation_status,status_err=err,
                    balance_before_lamports=balance_before,balance_after_lamports=balance_after,
                    observed_balance_delta_lamports=ctx.record.observed_balance_delta_lamports,
                )

            self.lifecycle.mark_confirmed(ctx,confirmation_status=confirmation.confirmation_status or "confirmed",
                                          slot=confirmation.slot,status_err=confirmation.err)
            balance_after=self._balance_lamports()
            self.lifecycle.mark_finalized(ctx,confirmation_status=confirmation.confirmation_status or "confirmed",
                                          slot=confirmation.slot,balance_after_lamports=balance_after)
            return response(
                success=True,lifecycle_id=ctx.record.lifecycle_id,state=ctx.record.state,signature=result.signature,
                reason="confirmed_and_reconciled",confirmation_status=confirmation.confirmation_status,
                status_err=confirmation.err,balance_before_lamports=balance_before,balance_after_lamports=balance_after,
                observed_balance_delta_lamports=ctx.record.observed_balance_delta_lamports,
            )
        except Exception as exc:
            err=f"{type(exc).__name__}:{str(exc)[:300]}"
            try: self.lifecycle.mark_failed(ctx,error=err)
            except Exception: pass
            return response(lifecycle_id=ctx.record.lifecycle_id,state=ctx.record.state,reason=err,status_err=err,
                            balance_before_lamports=balance_before)

