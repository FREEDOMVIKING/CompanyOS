from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Any
import json
import time
import uuid

from companyos.walletintegration.adaptive_solana_key import b58decode


@dataclass(frozen=True)
class ExecutionPolicy:
    daily_cap_sol: float = 200.0
    single_cap_sol: float = 150.0
    minimum_transfer_sol: float = 0.000001
    reserve_sol: float = 0.01
    require_destination_allowlist: bool = False
    allow_self_transfer: bool = True


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str
    amount_sol: float
    amount_lamports: int
    destination: str
    spent_today_sol: float
    remaining_daily_sol: float


class ExecutionAuditLedger:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or (Path.home() / ".companyos_runtime" / "execution_audit")
        self.root.mkdir(parents=True, exist_ok=True)

    def append(self, event: dict[str, Any]) -> Path:
        now = time.time()
        payload = dict(event)
        payload.setdefault("event_id", str(uuid.uuid4()))
        payload.setdefault("created_at_unix", now)
        day = time.strftime("%Y-%m-%d", time.localtime(now))
        day_dir = self.root / day
        day_dir.mkdir(parents=True, exist_ok=True)
        path = day_dir / f"{int(now*1000)}_{payload['event_id']}.json"
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(path)
        return path

    def spent_today_sol(self) -> float:
        day = time.strftime("%Y-%m-%d")
        day_dir = self.root / day
        if not day_dir.exists():
            return 0.0
        total = 0.0
        for p in day_dir.glob("*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            if data.get("event_type") != "transfer_finalized":
                continue
            try:
                total += float(data.get("amount_sol") or 0.0)
            except Exception:
                pass
        return total


class SolTransferExecutionPolicy:
    def __init__(
        self,
        policy: ExecutionPolicy,
        *,
        wallet_address: str,
        allowlist_path: Path | None = None,
        ledger: ExecutionAuditLedger | None = None,
    ) -> None:
        self.policy = policy
        self.wallet_address = wallet_address
        self.allowlist_path = allowlist_path
        self.ledger = ledger or ExecutionAuditLedger()

    @staticmethod
    def _valid_address(address: str) -> bool:
        try:
            raw = b58decode(address)
            return len(raw) == 32
        except Exception:
            return False

    def _allowlist(self) -> set[str]:
        if not self.allowlist_path or not self.allowlist_path.exists():
            return set()
        try:
            data = json.loads(self.allowlist_path.read_text(encoding="utf-8"))
        except Exception:
            return set()
        if isinstance(data, dict):
            data = data.get("addresses", [])
        return {str(x).strip() for x in data if str(x).strip()}

    def evaluate(self, destination: str, amount_lamports: int) -> PolicyDecision:
        destination = str(destination or "").strip()
        amount_lamports = int(amount_lamports)
        amount_sol = amount_lamports / 1_000_000_000

        spent = self.ledger.spent_today_sol()
        remaining = max(0.0, self.policy.daily_cap_sol - spent)

        def deny(reason: str) -> PolicyDecision:
            return PolicyDecision(
                False, reason, amount_sol, amount_lamports,
                destination, spent, remaining,
            )

        if amount_lamports <= 0:
            return deny("amount_must_be_positive")

        if not self._valid_address(destination):
            return deny("invalid_destination_address")

        if destination == self.wallet_address and not self.policy.allow_self_transfer:
            return deny("self_transfer_disallowed")

        if amount_sol < self.policy.minimum_transfer_sol:
            return deny("below_minimum_transfer")

        if amount_sol > self.policy.single_cap_sol:
            return deny("single_transaction_cap_exceeded")

        if amount_sol > remaining:
            return deny("daily_cap_exceeded")

        if self.policy.require_destination_allowlist:
            if destination not in self._allowlist():
                return deny("destination_not_allowlisted")

        return PolicyDecision(
            True, "policy_authorized", amount_sol, amount_lamports,
            destination, spent, remaining,
        )
