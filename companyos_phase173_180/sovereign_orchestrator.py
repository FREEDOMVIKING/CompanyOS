from datetime import datetime,timezone
from .world_model import WorldModel
from .decision_journal import DecisionJournal
from .counterfactual_engine import CounterfactualEngine
from .skill_factory import SkillFactory
from .workflow_composer import WorkflowComposer
from .metric_sentinel import MetricSentinel
from .succession_manager import SuccessionManager

class SovereignOrchestrator:
    """180: top-level self-directed internal orchestration and learning cycle."""
    def __init__(self):
        self.world=WorldModel();self.journal=DecisionJournal();self.counter=CounterfactualEngine()
        self.skills=SkillFactory();self.workflows=WorkflowComposer();self.metrics=MetricSentinel();self.succession=SuccessionManager()
    def run(self,p):
        scenarios=self.counter.rank(p.get("scenarios",[]))
        chosen=scenarios[0] if scenarios else None
        record=self.journal.record(chosen.get("name") if chosen else "continue_current_plan",
            "highest evidence-weighted internal option",chosen.get("counterfactual_score",0) if chosen else 0,True)
        return {"success":True,"status":"phase180_sovereign_orchestrator_completed",
        "timestamp":datetime.now(timezone.utc).isoformat(),
        "world_model":self.world.update(p.get("beliefs",[]),p.get("observations",[])),
        "ranked_scenarios":scenarios,"decision_record":record,
        "skill_proposals":self.skills.propose(p.get("executions",[])),
        "workflow":self.workflows.compose(p.get("objective","operate_company"),p.get("skills",[])),
        "metric_alerts":self.metrics.inspect(p.get("metrics",[])),
        "succession":self.succession.reassign(p.get("responsibilities",[]),p.get("agents",[])),
        "autonomy_mode":"high","self_directed_orchestration":True,
        "external_action_taken":False,"financial_action_taken":False,"irreversible_action_taken":False}
