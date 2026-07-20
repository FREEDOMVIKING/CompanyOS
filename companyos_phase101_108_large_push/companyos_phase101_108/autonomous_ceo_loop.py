from datetime import datetime,timezone
from .goal_tree import GoalTree
from .strategy_engine import StrategyEngine
from .delegation_supervisor import DelegationSupervisor
from .execution_watchdog import ExecutionWatchdog
from .economics_engine import EconomicsEngine
from .growth_loop import GrowthLoop
from .recovery_director import RecoveryDirector

class AutonomousCEOLoop:
    """108: closed-loop CEO planning/measurement layer with bounded external authority."""
    def __init__(self):
        self.goals=GoalTree();self.strategy=StrategyEngine();self.delegation=DelegationSupervisor()
        self.watchdog=ExecutionWatchdog();self.economics=EconomicsEngine();self.growth=GrowthLoop();self.recovery=RecoveryDirector()
    def run(self,p):
        return {"success":True,"status":"phase108_autonomous_ceo_loop_completed",
        "timestamp":datetime.now(timezone.utc).isoformat(),
        "goal_tree":self.goals.build(p.get("goal",""),p.get("objectives",[])),
        "strategies":self.strategy.rank(p.get("strategies",[])),
        "delegation_review":self.delegation.review(p.get("assignments",[])),
        "execution_health":self.watchdog.inspect(p.get("tasks",[])),
        "economics":self.economics.analyze(p.get("price",0),p.get("variable_cost",0),p.get("fixed_cost",0),p.get("customers",0)),
        "growth":self.growth.recommend(p.get("growth_metrics",{})),
        "external_action_taken":False,"financial_action_taken":False,"irreversible_action_taken":False}
