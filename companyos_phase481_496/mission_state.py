from dataclasses import dataclass, field, asdict

@dataclass
class MissionState:
    """481: canonical mission state for persistent CEO execution."""
    mission_id: str
    mission_type: str
    status: str = "queued"
    priority: float = 0.5
    attempts: int = 0
    max_attempts: int = 3
    blocked_on: list = field(default_factory=list)
    context: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)
