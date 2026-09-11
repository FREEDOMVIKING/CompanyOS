from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any

@dataclass
class LaunchProfile:
    name: str
    live_enabled: bool
    requires_operator_confirmation: bool
    max_single_action_amount: float
    max_daily_action_amount: float
    max_consecutive_failures: int
    external_actions_allowed: bool
    transaction_broadcasts_allowed: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def safe_profile() -> LaunchProfile:
    return LaunchProfile(
        name="SAFE",
        live_enabled=False,
        requires_operator_confirmation=True,
        max_single_action_amount=0.0,
        max_daily_action_amount=0.0,
        max_consecutive_failures=1,
        external_actions_allowed=False,
        transaction_broadcasts_allowed=False,
    )

def trial_profile(max_single: float, max_daily: float) -> LaunchProfile:
    return LaunchProfile(
        name="TRIAL_LIVE",
        live_enabled=True,
        requires_operator_confirmation=True,
        max_single_action_amount=max_single,
        max_daily_action_amount=max_daily,
        max_consecutive_failures=2,
        external_actions_allowed=True,
        transaction_broadcasts_allowed=True,
    )

def full_profile(max_single: float, max_daily: float, max_failures: int) -> LaunchProfile:
    return LaunchProfile(
        name="FULL_LIVE",
        live_enabled=True,
        requires_operator_confirmation=True,
        max_single_action_amount=max_single,
        max_daily_action_amount=max_daily,
        max_consecutive_failures=max_failures,
        external_actions_allowed=True,
        transaction_broadcasts_allowed=True,
    )
