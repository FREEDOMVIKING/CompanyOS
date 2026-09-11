from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Optional

from companyos.walletintegration.solana_rpc_preflight import rpc_call


@dataclass(frozen=True)
class ConfirmationResult:
    found: bool
    confirmed: bool
    finalized: bool
    confirmation_status: Optional[str]
    err: Any
    slot: Optional[int]
    polls: int
    elapsed_seconds: float


def wait_for_signature_status(
    rpc_url: str,
    signature: str,
    *,
    timeout_seconds: float = 45.0,
    poll_interval_seconds: float = 2.0,
) -> ConfirmationResult:
    start = time.time()
    polls = 0
    last = None

    while time.time() - start < timeout_seconds:
        polls += 1
        data = rpc_call(
            rpc_url,
            "getSignatureStatuses",
            [[signature], {"searchTransactionHistory": True}],
        )
        values = (data.get("result") or {}).get("value") or []
        status = values[0] if values else None

        if status:
            last = status
            confirmation = status.get("confirmationStatus")
            err = status.get("err")
            slot = status.get("slot")

            confirmed = confirmation in ("confirmed", "finalized") and err is None
            finalized = confirmation == "finalized" and err is None

            if confirmed:
                return ConfirmationResult(
                    found=True,
                    confirmed=True,
                    finalized=finalized,
                    confirmation_status=confirmation,
                    err=err,
                    slot=slot if isinstance(slot, int) else None,
                    polls=polls,
                    elapsed_seconds=time.time() - start,
                )

        time.sleep(max(0.5, poll_interval_seconds))

    confirmation = last.get("confirmationStatus") if isinstance(last, dict) else None
    err = last.get("err") if isinstance(last, dict) else None
    slot = last.get("slot") if isinstance(last, dict) else None

    return ConfirmationResult(
        found=last is not None,
        confirmed=False,
        finalized=False,
        confirmation_status=confirmation,
        err=err,
        slot=slot if isinstance(slot, int) else None,
        polls=polls,
        elapsed_seconds=time.time() - start,
    )
