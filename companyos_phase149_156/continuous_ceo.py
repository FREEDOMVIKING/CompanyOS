from datetime import datetime,timezone
from .goal_generator import GoalGenerator
from .market_feedback import MarketFeedbackLoop
from .product_manager import AutonomousProductManager
from .revenue_experimenter import RevenueExperimenter
from .knowledge_compounder import KnowledgeCompounder
from .resilience_manager import ResilienceManager
from .strategy_evolver import StrategyEvolver

class ContinuousCEO:
    """156: continuous autonomous CEO reasoning/execution cycle."""
    def __init__(self):
        self.goals=GoalGenerator(); self.feedback=MarketFeedbackLoop()
        self.product=AutonomousProductManager(); self.revenue=RevenueExperimenter()
        self.knowledge=KnowledgeCompounder(); self.resilience=ResilienceManager()
        self.strategy=StrategyEvolver()

    def run(self,p):
        return {
          "success":True,"status":"phase156_continuous_ceo_completed",
          "timestamp":datetime.now(timezone.utc).isoformat(),
          "generated_goals":self.goals.generate(p.get("mission"),p.get("state",{})),
          "market_feedback":self.feedback.analyze(p.get("signals",[])),
          "product_priorities":self.product.prioritize(p.get("backlog",[]),p.get("capacity",5)),
          "revenue_experiment":self.revenue.design(p.get("revenue_hypothesis","test_offer"),p.get("experiment_budget",0)),
          "knowledge":self.knowledge.compound(p.get("observations",[])),
          "resilience":self.resilience.respond(p.get("failure",{})),
          "strategy":self.strategy.evolve(p.get("strategies",[])),
          "autonomy_mode":"high",
          "external_action_taken":False,"financial_action_taken":False,"irreversible_action_taken":False
        }
