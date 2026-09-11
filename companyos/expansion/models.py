from dataclasses import dataclass, asdict
from typing import Dict, Any

@dataclass
class ActionProposal:
    action_id: str
    capability: str
    action: str
    payload: Dict[str, Any]
    risk_level: str = "medium"
    approval_required: bool = True
    execution_mode: str = "proposal_only"
    status: str = "queued"

    def to_dict(self):
        return asdict(self)
