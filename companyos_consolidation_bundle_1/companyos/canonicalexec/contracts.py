from dataclasses import dataclass, field, asdict
from typing import Any, Dict
import time, uuid

@dataclass
class ExecutionRequest:
    action: str
    payload: Dict[str, Any] = field(default_factory=dict)
    source: str = "companyos"
    requires_human_approval: bool = False
    external_action: bool = False
    financial_action: bool = False
    idempotency_key: str = ""
    created_at: float = field(default_factory=time.time)
    def __post_init__(self):
        if not self.idempotency_key:
            self.idempotency_key = str(uuid.uuid4())
    def to_dict(self):
        return asdict(self)

@dataclass
class ExecutionResult:
    accepted: bool
    status: str
    mode: str
    request_id: str
    message: str = ""
    receipt: Dict[str, Any] = field(default_factory=dict)
    external_action_performed: bool = False
    transaction_broadcast_performed: bool = False
    def to_dict(self):
        return asdict(self)
