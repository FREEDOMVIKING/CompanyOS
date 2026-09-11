from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class SolanaRpcPreflightResult:
    rpc_reachable: bool
    genesis_hash_available: bool
    latest_blockhash_available: bool
    wallet_balance_lamports: Optional[int]
    wallet_balance_sol: Optional[float]
    error: Optional[str]


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


def run_rpc_preflight(rpc_url: str, wallet_address: str) -> SolanaRpcPreflightResult:
    try:
        genesis = rpc_call(rpc_url, "getGenesisHash")
        blockhash = rpc_call(
            rpc_url,
            "getLatestBlockhash",
            [{"commitment": "confirmed"}],
        )
        balance = rpc_call(
            rpc_url,
            "getBalance",
            [wallet_address, {"commitment": "confirmed"}],
        )

        genesis_ok = bool(genesis.get("result"))
        blockhash_ok = bool(
            (blockhash.get("result") or {}).get("value", {}).get("blockhash")
        )
        lamports = (balance.get("result") or {}).get("value")
        sol = (lamports / 1_000_000_000) if isinstance(lamports, int) else None

        return SolanaRpcPreflightResult(
            rpc_reachable=True,
            genesis_hash_available=genesis_ok,
            latest_blockhash_available=blockhash_ok,
            wallet_balance_lamports=lamports if isinstance(lamports, int) else None,
            wallet_balance_sol=sol,
            error=None,
        )
    except Exception as exc:
        return SolanaRpcPreflightResult(
            rpc_reachable=False,
            genesis_hash_available=False,
            latest_blockhash_available=False,
            wallet_balance_lamports=None,
            wallet_balance_sol=None,
            error=f"{type(exc).__name__}:{str(exc)[:240]}",
        )
