from datetime import datetime,timezone
from .decision_quality import DecisionQuality
from .process_optimizer import ProcessOptimizer
from .risk_register import RiskRegister
from .scenario_planner import ScenarioPlanner
from .portfolio_governor import PortfolioGovernor
class CEOOrchestrator:
    """92: executive synthesis layer for bounded autonomous CEO decisions."""
    def __init__(self):
        self.quality=DecisionQuality();self.process=ProcessOptimizer()
        self.risks=RiskRegister();self.scenarios=ScenarioPlanner();self.portfolio=PortfolioGovernor()
    def run(self,p):
        decisions=[{**d,"quality":self.quality.score(d)} for d in p.get("decisions",[])]
        return {"success":True,"status":"phase92_ceo_cycle_completed",
        "timestamp":datetime.now(timezone.utc).isoformat(),"decisions":decisions,
        "process":self.process.analyze(p.get("process_steps",[])),
        "risks":self.risks.assess(p.get("risks",[])),
        "scenario":self.scenarios.build(p.get("base_value",0),p.get("upside",.25),p.get("downside",.25)),
        "portfolio":self.portfolio.review(p.get("ventures",[])),
        "external_action_taken":False,"irreversible_action_taken":False}
