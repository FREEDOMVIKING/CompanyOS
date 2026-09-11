from __future__ import annotations

import json
import time
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional


LAMPORTS_PER_SOL = 1_000_000_000


@dataclass
class TreasurySnapshot:
    wallet_address: str
    sol_balance: float
    sol_lamports: int
    fetched_at_unix: float
    rpc_ok: bool
    rpc_error: Optional[str]
    stale: bool
    age_seconds: float
    reserve_sol: float
    spendable_sol: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def rpc_call(url: str, method: str, params: list[Any] | None = None, timeout: int = 20) -> dict:
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or [],
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    if "error" in data:
        raise RuntimeError(f"rpc_error:{data['error']}")
    return data


class LiveTreasuryFeed:
    def __init__(
        self,
        rpc_url: str,
        wallet_address: str,
        *,
        reserve_sol: float = 0.0,
        stale_after_seconds: float = 60.0,
        state_path: Path | None = None,
    ) -> None:
        self.rpc_url = rpc_url
        self.wallet_address = wallet_address
        self.reserve_sol = max(0.0, float(reserve_sol))
        self.stale_after_seconds = max(1.0, float(stale_after_seconds))
        self.state_path = state_path or (
            Path.home() / ".companyos_runtime" / "treasury_live_state.json"
        )

    def fetch(self) -> TreasurySnapshot:
        now = time.time()
        try:
            result = rpc_call(
                self.rpc_url,
                "getBalance",
                [self.wallet_address, {"commitment": "confirmed"}],
            )
            lamports = int((result.get("result") or {}).get("value"))
            sol = lamports / LAMPORTS_PER_SOL
            spendable = max(0.0, sol - self.reserve_sol)

            snap = TreasurySnapshot(
                wallet_address=self.wallet_address,
                sol_balance=sol,
                sol_lamports=lamports,
                fetched_at_unix=now,
                rpc_ok=True,
                rpc_error=None,
                stale=False,
                age_seconds=0.0,
                reserve_sol=self.reserve_sol,
                spendable_sol=spendable,
            )
            self._persist(snap)
            return snap
        except Exception as exc:
            prior = self.load_cached()
            if prior:
                age = max(0.0, now - float(prior.fetched_at_unix))
                prior.rpc_ok = False
                prior.rpc_error = f"{type(exc).__name__}:{str(exc)[:240]}"
                prior.stale = age >= self.stale_after_seconds
                prior.age_seconds = age
                return prior

            return TreasurySnapshot(
                wallet_address=self.wallet_address,
                sol_balance=0.0,
                sol_lamports=0,
                fetched_at_unix=0.0,
                rpc_ok=False,
                rpc_error=f"{type(exc).__name__}:{str(exc)[:240]}",
                stale=True,
                age_seconds=float("inf"),
                reserve_sol=self.reserve_sol,
                spendable_sol=0.0,
            )

    def force_fresh_before_financial_action(self) -> TreasurySnapshot:
        """
        Call this immediately before a financial authorization/execution decision.
        No stale cached snapshot is accepted as fresh.
        """
        snap = self.fetch()
        if not snap.rpc_ok:
            raise RuntimeError("live_treasury_refresh_failed")
        if snap.stale:
            raise RuntimeError("live_treasury_state_stale")
        return snap

    def _persist(self, snap: TreasurySnapshot) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        tmp.write_text(json.dumps(snap.to_dict(), indent=2) + "\n", encoding="utf-8")
        tmp.replace(self.state_path)

    def load_cached(self) -> TreasurySnapshot | None:
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            now = time.time()
            age = max(0.0, now - float(data.get("fetched_at_unix", 0.0)))
            return TreasurySnapshot(
                wallet_address=str(data["wallet_address"]),
                sol_balance=float(data["sol_balance"]),
                sol_lamports=int(data["sol_lamports"]),
                fetched_at_unix=float(data["fetched_at_unix"]),
                rpc_ok=bool(data.get("rpc_ok", False)),
                rpc_error=data.get("rpc_error"),
                stale=age >= self.stale_after_seconds,
                age_seconds=age,
                reserve_sol=float(data.get("reserve_sol", self.reserve_sol)),
                spendable_sol=float(data.get("spendable_sol", 0.0)),
            )
        except Exception:
            return None
