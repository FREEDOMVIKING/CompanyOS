from dataclasses import dataclass, asdict

@dataclass
class LaunchDecision:
    review_id: str
    venture_id: str
    venture_name: str
    decision: str
    reason: str
    actor: str
    created_at: str
    source_launch_score: float
    previous_status: str
    new_status: str
    decision_hash: str = ""

    def to_dict(self):
        return asdict(self)
