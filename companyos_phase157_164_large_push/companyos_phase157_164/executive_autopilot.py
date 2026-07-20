from datetime import datetime,timezone
from .mission_planner import MissionPlanner
from .dependency_orchestrator import DependencyOrchestrator
from .delegation_director import DelegationDirector
from .execution_memory import ExecutionMemory
from .adaptive_budgeter import AdaptiveBudgeter
from .quality_governor import QualityGovernor
from .stagnation_breaker import StagnationBreaker

class ExecutiveAutopilot:
    """164: persistent autonomous executive orchestration cycle."""
    def __init__(self):
        self.planner=MissionPlanner(); self.deps=DependencyOrchestrator(); self.delegate=DelegationDirector()
        self.memory=ExecutionMemory(); self.budget=AdaptiveBudgeter(); self.quality=QualityGovernor(); self.stagnation=StagnationBreaker()
    def run(self,p):
        missions=self.planner.plan(p.get("objectives",[]))
        ready=self.deps.ready(p.get("tasks",[]),p.get("completed",[]))
        return {"success":True,"status":"phase164_executive_autopilot_completed",
          "timestamp":datetime.now(timezone.utc).isoformat(),"missions":missions,"ready_tasks":ready,
          "delegated":self.delegate.delegate(ready,p.get("agents",[])),
          "execution_memory":self.memory.summarize(p.get("runs",[])),
          "allocations":self.budget.allocate(p.get("ventures",[]),p.get("internal_capacity",0)),
          "quality":self.quality.evaluate(p.get("candidate_output",{})),
          "stagnation":self.stagnation.decide(p.get("history",[])),
          "autonomy_mode":"high","continuous_operation":True,
          "external_action_taken":False,"financial_action_taken":False,"irreversible_action_taken":False}
