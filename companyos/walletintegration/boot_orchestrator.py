from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any

from companyos.walletintegration.solana_signer_key_adapter import load_signer_material
from companyos.walletintegration.live_treasury_feed import LiveTreasuryFeed
from companyos.walletintegration.startup_reconciliation_gate import StartupReconciliationGate


@dataclass(frozen=True)
class BootReadinessResult:
    ready: bool
    reason: str
    env_file: str
    wallet_address: Optional[str]
    rpc_configured: bool
    key_configured: bool
    wallet_derived: bool
    live_balance_ok: bool
    live_balance_sol: Optional[float]
    startup_reconciliation_ok: bool
    unresolved_records: int
    signed_pending_records: int
    private_key_printed: bool
    broadcast_attempted: bool


class CompanyOSBootOrchestrator:
    """
    Production startup readiness sequence.

    Order:
      1) locate runtime env
      2) validate RPC/key presence
      3) derive wallet identity
      4) force fresh live treasury read
      5) run startup reconciliation gate
      6) return READY/BLOCKED

    This orchestrator NEVER builds, signs, or broadcasts transactions.
    """

    ENV_CANDIDATES = (
        Path.home() / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / "companyos_runtime" / "live_financial.env",
    )

    def _load_env(self):
        p = next((x for x in self.ENV_CANDIDATES if x.exists()), None)
        if p is None:
            return None, {}

        cfg = {}
        for line in p.read_text(errors="ignore").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip().strip("'\"")
        return p, cfg

    def run(self) -> BootReadinessResult:
        env_path, cfg = self._load_env()
        if env_path is None:
            return BootReadinessResult(
                ready=False,
                reason="runtime_env_missing",
                env_file="",
                wallet_address=None,
                rpc_configured=False,
                key_configured=False,
                wallet_derived=False,
                live_balance_ok=False,
                live_balance_sol=None,
                startup_reconciliation_ok=False,
                unresolved_records=0,
                signed_pending_records=0,
                private_key_printed=False,
                broadcast_attempted=False,
            )

        rpc = cfg.get("SOLANA_RPC_URL", "").strip()
        secret = cfg.get("SOLANA_PRIVATE_KEY", "").strip()
        encoding = cfg.get("SOLANA_PRIVATE_KEY_ENCODING", "auto").strip()
        reserve = float(cfg.get("COMPANYOS_LIVE_MIN_RESERVE", "0") or 0)

        if not rpc:
            return BootReadinessResult(
                False, "rpc_missing", str(env_path), None,
                False, bool(secret), False, False, None,
                False, 0, 0, False, False
            )

        if not secret:
            return BootReadinessResult(
                False, "private_key_missing", str(env_path), None,
                True, False, False, False, None,
                False, 0, 0, False, False
            )

        try:
            material = load_signer_material(secret, encoding)
        except Exception as exc:
            return BootReadinessResult(
                False, f"wallet_derivation_failed:{type(exc).__name__}",
                str(env_path), None, True, True, False,
                False, None, False, 0, 0, False, False
            )

        wallet = material.public_address
        if not wallet:
            return BootReadinessResult(
                False, "wallet_address_unavailable",
                str(env_path), None, True, True, False,
                False, None, False, 0, 0, False, False
            )

        feed = LiveTreasuryFeed(
            rpc,
            wallet,
            reserve_sol=reserve,
            stale_after_seconds=60,
        )

        try:
            snap = feed.force_fresh_before_financial_action()
            balance_ok = bool(snap.rpc_ok and not snap.stale)
            balance_sol = snap.sol_balance
        except Exception:
            balance_ok = False
            balance_sol = None

        if not balance_ok:
            return BootReadinessResult(
                False, "live_balance_unavailable",
                str(env_path), wallet, True, True, True,
                False, balance_sol, False, 0, 0, False, False
            )

        gate = StartupReconciliationGate(rpc_url=rpc)
        gate_result = gate.evaluate()

        ready = bool(gate_result.allowed_to_resume)
        reason = (
            "boot_readiness_clear"
            if ready
            else "startup_reconciliation_blocked"
        )

        return BootReadinessResult(
            ready=ready,
            reason=reason,
            env_file=str(env_path),
            wallet_address=wallet,
            rpc_configured=True,
            key_configured=True,
            wallet_derived=True,
            live_balance_ok=True,
            live_balance_sol=balance_sol,
            startup_reconciliation_ok=gate_result.allowed_to_resume,
            unresolved_records=gate_result.unresolved_records,
            signed_pending_records=gate_result.signed_pending_records,
            private_key_printed=False,
            broadcast_attempted=False,
        )
