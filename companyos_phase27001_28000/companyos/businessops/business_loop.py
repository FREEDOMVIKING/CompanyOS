from .venture_engine import VentureEngine
from .launch_gate import LaunchGate
from .revenue_tracker import RevenueTracker
from .portfolio_policy import PortfolioPolicy

class AutonomousBusinessLoop:
    def __init__(self, root, ceo_finance_loop=None):
        self.root = root
        self.ceo_finance_loop = ceo_finance_loop
        self.revenue = RevenueTracker(root)

    def evaluate(self, candidates, build_result=None, available_capital=0, reserve_floor=0):
        ranked = VentureEngine().select(candidates)
        selected = ranked[0] if ranked else None
        if not selected:
            return {"success":False,"status":"no_venture_candidates"}

        finance = None
        if self.ceo_finance_loop:
            finance = self.ceo_finance_loop.evaluate_opportunities(
                [selected],
                available_capital=available_capital,
                reserve_floor=reserve_floor
            )

        gate = LaunchGate().evaluate(
            selected,
            build_result or {"success":False},
            finance or {}
        )

        metrics = self.revenue.summary(selected.get("id") or selected.get("name"))
        portfolio = PortfolioPolicy().decide(metrics)

        return {
            "success": True,
            "selected_venture": selected,
            "finance": finance,
            "launch_gate": gate,
            "metrics": metrics,
            "portfolio_decision": portfolio
        }
