from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Any

from companyos.walletintegration.boot_orchestrator import CompanyOSBootOrchestrator
from companyos.walletintegration.startup_reconciliation_gate import StartupReconciliationGate
from companyos.walletintegration.live_treasury_feed import LiveTreasuryFeed
from companyos.walletintegration.solana_signer_key_adapter import load_signer_material


@dataclass
class RuntimeSupervisorState:
    running: bool
    ready: bool
    reason: str
    started_at_unix: float
    last_cycle_unix: float
    cycle_count: int
    rpc_ok: bool
    stale: bool
    wallet_address: Optional[str]
    sol_balance: Optional[float]
    spendable_sol: Optional[float]
    unresolved_records: int
    signed_pending_records: int
    consecutive_failures: int
    broadcast_attempted: bool
    private_key_printed: bool


class ProductionRuntimeSupervisor:
    """
    Long-running CompanyOS production runtime supervisor.

    Responsibilities:
    - enforce Phase 88 boot readiness before runtime starts
    - refresh live treasury state continuously
    - rerun startup/recovery reconciliation checks
    - track runtime health and consecutive failures
    - persist supervisor state atomically
    - never build/sign/broadcast transactions itself

    Financial execution remains delegated to the execution coordinator.
    """

    def __init__(
        self,
        *,
        interval_seconds: float = 20.0,
        state_path: Path | None = None,
        max_consecutive_failures: int = 5,
    ) -> None:
        self.interval_seconds = max(5.0, float(interval_seconds))
        self.max_consecutive_failures = max(1, int(max_consecutive_failures))
        self.state_path = state_path or (
            Path.home() / ".companyos_runtime" / "production_runtime_supervisor.json"
        )
        self._stop_requested = False

    def request_stop(self) -> None:
        self._stop_requested = True

    def _load_env(self):
        candidates = [
            Path.home() / ".companyos_runtime" / "live_financial.env",
            Path.home() / "companyos" / ".companyos_runtime" / "live_financial.env",
            Path.home() / "companyos" / "companyos_runtime" / "live_financial.env",
        ]
        p = next((x for x in candidates if x.exists()), None)
        if p is None:
            raise RuntimeError("live_financial_env_missing")

        cfg = {}
        for line in p.read_text(errors="ignore").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip().strip("'\"")
        return p, cfg

    def _persist(self, state: RuntimeSupervisorState) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        tmp.write_text(json.dumps(asdict(state), indent=2) + "\n", encoding="utf-8")
        tmp.replace(self.state_path)

    def startup(self) -> tuple[RuntimeSupervisorState, LiveTreasuryFeed, StartupReconciliationGate]:
        boot = CompanyOSBootOrchestrator().run()
        now = time.time()

        if not boot.ready:
            state = RuntimeSupervisorState(
                running=False,
                ready=False,
                reason=boot.reason,
                started_at_unix=now,
                last_cycle_unix=now,
                cycle_count=0,
                rpc_ok=False,
                stale=True,
                wallet_address=boot.wallet_address,
                sol_balance=boot.live_balance_sol,
                spendable_sol=None,
                unresolved_records=boot.unresolved_records,
                signed_pending_records=boot.signed_pending_records,
                consecutive_failures=1,
                broadcast_attempted=False,
                private_key_printed=False,
            )
            self._persist(state)
            raise RuntimeError(f"boot_blocked:{boot.reason}")

        _, cfg = self._load_env()
        rpc = cfg["SOLANA_RPC_URL"]
        secret = cfg["SOLANA_PRIVATE_KEY"]
        enc = cfg.get("SOLANA_PRIVATE_KEY_ENCODING", "auto")
        reserve = float(cfg.get("COMPANYOS_LIVE_MIN_RESERVE", "0") or 0)

        material = load_signer_material(secret, enc)
        feed = LiveTreasuryFeed(
            rpc,
            material.public_address,
            reserve_sol=reserve,
            stale_after_seconds=max(60.0, self.interval_seconds * 3),
        )
        gate = StartupReconciliationGate(rpc_url=rpc)

        snap = feed.force_fresh_before_financial_action()
        gate_result = gate.evaluate()

        state = RuntimeSupervisorState(
            running=True,
            ready=gate_result.allowed_to_resume,
            reason="runtime_started" if gate_result.allowed_to_resume else "reconciliation_blocked",
            started_at_unix=now,
            last_cycle_unix=now,
            cycle_count=0,
            rpc_ok=snap.rpc_ok,
            stale=snap.stale,
            wallet_address=material.public_address,
            sol_balance=snap.sol_balance,
            spendable_sol=snap.spendable_sol,
            unresolved_records=gate_result.unresolved_records,
            signed_pending_records=gate_result.signed_pending_records,
            consecutive_failures=0,
            broadcast_attempted=False,
            private_key_printed=False,
        )
        self._persist(state)

        if not state.ready:
            raise RuntimeError("startup_reconciliation_blocked")

        return state, feed, gate

    def cycle(
        self,
        state: RuntimeSupervisorState,
        feed: LiveTreasuryFeed,
        gate: StartupReconciliationGate,
    ) -> RuntimeSupervisorState:
        now = time.time()
        try:
            snap = feed.fetch()
            gate_result = gate.evaluate()

            healthy = bool(
                snap.rpc_ok
                and not snap.stale
                and gate_result.allowed_to_resume
            )

            state.running = True
            state.ready = healthy
            state.reason = "healthy" if healthy else "runtime_health_blocked"
            state.last_cycle_unix = now
            state.cycle_count += 1
            state.rpc_ok = snap.rpc_ok
            state.stale = snap.stale
            state.sol_balance = snap.sol_balance
            state.spendable_sol = snap.spendable_sol
            state.unresolved_records = gate_result.unresolved_records
            state.signed_pending_records = gate_result.signed_pending_records
            state.consecutive_failures = 0 if healthy else state.consecutive_failures + 1
            state.broadcast_attempted = False
            state.private_key_printed = False
        except Exception as exc:
            state.running = True
            state.ready = False
            state.reason = f"cycle_error:{type(exc).__name__}"
            state.last_cycle_unix = now
            state.cycle_count += 1
            state.consecutive_failures += 1
            state.broadcast_attempted = False
            state.private_key_printed = False

        self._persist(state)
        return state

    def run_forever(self) -> None:
        state, feed, gate = self.startup()

        print("COMPANYOS_PRODUCTION_RUNTIME_SUPERVISOR: STARTED")
        print("WALLET_ADDRESS:", state.wallet_address)
        print("INTERVAL_SECONDS:", self.interval_seconds)
        print("BROADCAST_BY_SUPERVISOR: False")

        while not self._stop_requested:
            state = self.cycle(state, feed, gate)

            print(
                f"CYCLE={state.cycle_count} "
                f"READY={state.ready} "
                f"RPC_OK={state.rpc_ok} "
                f"STALE={state.stale} "
                f"SOL={state.sol_balance} "
                f"SPENDABLE={state.spendable_sol} "
                f"UNRESOLVED={state.unresolved_records} "
                f"FAILURES={state.consecutive_failures}"
            )

            if state.consecutive_failures >= self.max_consecutive_failures:
                state.running = False
                state.reason = "max_consecutive_failures_reached"
                self._persist(state)
                raise RuntimeError(state.reason)

            time.sleep(self.interval_seconds)
