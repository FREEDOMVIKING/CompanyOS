from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from companyos.walletintegration.solana_rpc_preflight import rpc_call


@dataclass(frozen=True)
class SimulationResult:
    rpc_ok: bool
    simulation_ok: bool
    err: Any
    logs: list[str]
    units_consumed: Optional[int]
    replacement_blockhash_used: bool


def simulate_signed_transaction(
    rpc_url: str,
    transaction_base64: str,
    *,
    commitment: str = "confirmed",
) -> SimulationResult:
    """
    Simulate a fully signed Solana transaction.

    This function NEVER calls sendTransaction and therefore does not broadcast.
    It is intended for preflight validation only.
    """
    params = [
        transaction_base64,
        {
            "encoding": "base64",
            "sigVerify": True,
            "replaceRecentBlockhash": False,
            "commitment": commitment,
        },
    ]

    try:
        data = rpc_call(rpc_url, "simulateTransaction", params)
        value = (data.get("result") or {}).get("value") or {}

        err = value.get("err")
        logs = value.get("logs") or []
        units = value.get("unitsConsumed")

        return SimulationResult(
            rpc_ok=True,
            simulation_ok=(err is None),
            err=err,
            logs=list(logs),
            units_consumed=units if isinstance(units, int) else None,
            replacement_blockhash_used=False,
        )
    except Exception as exc:
        return SimulationResult(
            rpc_ok=False,
            simulation_ok=False,
            err=f"{type(exc).__name__}:{str(exc)[:300]}",
            logs=[],
            units_consumed=None,
            replacement_blockhash_used=False,
        )
