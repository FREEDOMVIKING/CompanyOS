from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional


VALID_STATES = {
    "AUTHORIZED",
    "SIGNED",
    "SUBMITTED",
    "CONFIRMED",
    "FINALIZED",
    "FAILED",
}


@dataclass
class TransactionLifecycleRecord:
    lifecycle_id: str
    wallet_address: str
    destination: str
    requested_lamports: int
    state: str
    signature: Optional[str]
    created_at_unix: float
    updated_at_unix: float
    balance_before_lamports: Optional[int]
    balance_after_lamports: Optional[int]
    observed_balance_delta_lamports: Optional[int]
    status_err: Any
    confirmation_status: Optional[str]
    slot: Optional[int]
    metadata: dict[str, Any]


class TransactionLifecycleStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or (Path.home() / ".companyos_runtime" / "transaction_lifecycle")
        self.root.mkdir(parents=True, exist_ok=True)

    def new(
        self,
        *,
        wallet_address: str,
        destination: str,
        requested_lamports: int,
        balance_before_lamports: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TransactionLifecycleRecord:
        now = time.time()
        record = TransactionLifecycleRecord(
            lifecycle_id=str(uuid.uuid4()),
            wallet_address=wallet_address,
            destination=destination,
            requested_lamports=int(requested_lamports),
            state="AUTHORIZED",
            signature=None,
            created_at_unix=now,
            updated_at_unix=now,
            balance_before_lamports=balance_before_lamports,
            balance_after_lamports=None,
            observed_balance_delta_lamports=None,
            status_err=None,
            confirmation_status=None,
            slot=None,
            metadata=metadata or {},
        )
        self.save(record)
        return record

    def transition(self, record: TransactionLifecycleRecord, state: str, **updates: Any) -> TransactionLifecycleRecord:
        state = state.upper().strip()
        if state not in VALID_STATES:
            raise ValueError(f"invalid_state:{state}")

        record.state = state
        record.updated_at_unix = time.time()

        for key, value in updates.items():
            if not hasattr(record, key):
                raise AttributeError(f"unknown_lifecycle_field:{key}")
            setattr(record, key, value)

        if (
            record.balance_before_lamports is not None
            and record.balance_after_lamports is not None
        ):
            record.observed_balance_delta_lamports = (
                record.balance_before_lamports - record.balance_after_lamports
            )

        self.save(record)
        return record

    def save(self, record: TransactionLifecycleRecord) -> None:
        path = self.root / f"{record.lifecycle_id}.json"
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(asdict(record), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(path)

    def load(self, lifecycle_id: str) -> TransactionLifecycleRecord:
        path = self.root / f"{lifecycle_id}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return TransactionLifecycleRecord(**data)
