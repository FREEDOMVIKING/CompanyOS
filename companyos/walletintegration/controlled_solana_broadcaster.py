from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from companyos.walletintegration.solana_rpc_preflight import rpc_call


@dataclass(frozen=True)
class BroadcastResult:
    submitted: bool
    signature: Optional[str]
    rpc_ok: bool
    error: Optional[str]


class ControlledSolanaBroadcaster:
    """
    Explicitly gated Solana sendTransaction wrapper.

    IMPORTANT:
    - This module never broadcasts unless `broadcast_enabled=True`.
    - The caller must pass an explicit `confirm_token`.
    - Intended to sit behind CompanyOS execution authorization.
    """

    REQUIRED_CONFIRM_TOKEN = "BROADCAST_ZERO_SELF_TRANSFER"

    def __init__(self, rpc_url: str, *, broadcast_enabled: bool = False) -> None:
        self.rpc_url = rpc_url
        self.broadcast_enabled = bool(broadcast_enabled)

    def send_serialized_transaction(
        self,
        transaction_base64: str,
        *,
        confirm_token: str = "",
        skip_preflight: bool = False,
        preflight_commitment: str = "confirmed",
        max_retries: int = 3,
    ) -> BroadcastResult:

        if not self.broadcast_enabled:
            return BroadcastResult(
                submitted=False,
                signature=None,
                rpc_ok=True,
                error="broadcast_disabled",
            )

        if confirm_token != self.REQUIRED_CONFIRM_TOKEN:
            return BroadcastResult(
                submitted=False,
                signature=None,
                rpc_ok=True,
                error="explicit_confirmation_required",
            )

        try:
            data = rpc_call(
                self.rpc_url,
                "sendTransaction",
                [
                    transaction_base64,
                    {
                        "encoding": "base64",
                        "skipPreflight": bool(skip_preflight),
                        "preflightCommitment": preflight_commitment,
                        "maxRetries": int(max_retries),
                    },
                ],
            )
            sig = data.get("result")
            return BroadcastResult(
                submitted=bool(sig),
                signature=sig if isinstance(sig, str) else None,
                rpc_ok=True,
                error=None if sig else "missing_signature",
            )
        except Exception as exc:
            return BroadcastResult(
                submitted=False,
                signature=None,
                rpc_ok=False,
                error=f"{type(exc).__name__}:{str(exc)[:300]}",
            )
