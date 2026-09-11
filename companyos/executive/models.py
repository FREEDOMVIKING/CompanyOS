from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any


@dataclass
class Venture:
    venture_id: str
    name: str
    stage: str = "discovery"
    expected_return: float = 0.0
    confidence: float = 0.5
    risk: float = 0.5
    urgency: float = 0.5
    strategic_fit: float = 0.5
    capital_requested: float = 0.0
    workers_requested: int = 1
    progress: float = 0.0
    failure_probability: float = 0.1
    dependencies: List[str] = field(default_factory=list)
    blocked: bool = False
    metrics: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Worker:
    worker_id: str
    specialty: str
    capacity: float = 1.0
    current_load: float = 0.0
    reliability: float = 0.8

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AllocationDecision:
    venture_id: str
    priority_score: float
    capital_proposed: float
    workers_proposed: List[str]
    scale_action: str
    approval_required: bool
    reasons: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
