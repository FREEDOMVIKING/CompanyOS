from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import uuid

@dataclass
class FinancialIntent:
    chain: str
    amount: float
    destination: str
    purpose: str
    source: str | None = None
    token_mint: str | None = None
    token_contract: str | None = None
    idempotency_key: str | None = None

    def normalize(self):
        if not self.idempotency_key:
            self.idempotency_key = "finintent_" + uuid.uuid4().hex
        row = asdict(self)
        row["created_at"] = datetime.now(timezone.utc).isoformat()
        row["chain"] = str(self.chain).lower().strip()
        row["amount"] = float(self.amount)
        row["destination"] = str(self.destination).strip()
        return row
