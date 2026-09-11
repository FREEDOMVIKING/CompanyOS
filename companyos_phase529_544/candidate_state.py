from dataclasses import dataclass, asdict

@dataclass
class CandidateState:
    """537: persistent lifecycle state for opportunity candidates."""
    name: str
    theme: str
    status: str = "scored"
    decision: str = "research_more"
    quality_score: float = 0.0
    source_count: int = 0

    def to_dict(self):
        return asdict(self)
