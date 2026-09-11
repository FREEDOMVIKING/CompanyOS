from dataclasses import dataclass, field, asdict

@dataclass
class VentureState:
    """433: persistent venture lifecycle state."""
    venture_id: str
    name: str
    status: str = "queued"
    priority: float = 0.5
    stage: str = "incubating"
    build_cycles: int = 0
    failures: int = 0
    retries: int = 0
    blocked_reason: str | None = None
    metrics: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)
