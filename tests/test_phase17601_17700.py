from pathlib import Path
import sys

ROOT = Path.home() / "companyos"
sys.path.insert(0, str(ROOT))

from companyos_modules.phase17601_17700.portfolio_director import (
    AutonomousPortfolioDirector,
    VentureState,
)


def venture(
    venture_id: str,
    revenue: float,
    cost: float,
    growth: float,
    risk: float,
    health: float,
):
    return VentureState(
        venture_id=venture_id,
        name=venture_id,
        monthly_revenue=revenue,
        monthly_cost=cost,
        growth_rate=growth,
        confidence=0.8,
        strategic_fit=0.85,
        risk=risk,
        execution_health=health,
    )


def test_profitable_venture_ranks_first():
    director = AutonomousPortfolioDirector(
        ROOT / "companyos_runtime" / "phase17601_17700_test"
    )
    strong = venture("strong", 50000, 15000, 0.2, 0.2, 0.9)
    weak = venture("weak", 5000, 12000, -0.1, 0.6, 0.4)
    ranked = director.rank_ventures([weak, strong])
    assert ranked[0]["venture"]["venture_id"] == "strong"


def test_portfolio_decision_actions():
    director = AutonomousPortfolioDirector(
        ROOT / "companyos_runtime" / "phase17601_17700_test"
    )
    strong = venture("strong", 50000, 15000, 0.2, 0.2, 0.9)
    weak = venture("weak", 5000, 12000, -0.1, 0.7, 0.3)
    assert director.decide(strong).action in {"scale", "continue"}
    assert director.decide(weak).action in {"repair", "pause"}


def test_capital_plan_never_transfers_funds():
    director = AutonomousPortfolioDirector(
        ROOT / "companyos_runtime" / "phase17601_17700_test"
    )
    plans = director.allocate_capital(
        [
            venture("a", 30000, 10000, 0.15, 0.2, 0.8),
            venture("b", 18000, 9000, 0.05, 0.3, 0.7),
        ],
        available_budget=20000,
    )
    assert round(sum(plan.recommended_budget for plan in plans), 2) <= 16000
    state = (
        ROOT
        / "companyos_runtime"
        / "phase17601_17700_test"
        / "latest_capital_plan.json"
    ).read_text(encoding="utf-8")
    assert '"funds_transferred": false' in state
    assert '"requires_existing_financial_approval_gates": true' in state
