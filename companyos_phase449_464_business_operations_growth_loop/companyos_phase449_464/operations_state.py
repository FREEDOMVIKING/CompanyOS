from dataclasses import dataclass, field, asdict

@dataclass
class OperationsState:
    """450: persistent operational state for a launched venture."""
    venture_id: str
    stage: str = "limited_beta"
    active_users: int = 0
    paying_customers: int = 0
    mrr: float = 0.0
    churn_rate: float = 0.0
    support_incidents: int = 0
    experiments_running: int = 0
    metrics: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)
