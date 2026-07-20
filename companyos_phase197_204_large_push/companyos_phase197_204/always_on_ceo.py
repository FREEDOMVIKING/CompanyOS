from datetime import datetime,timezone
from .goal_continuity import GoalContinuityEngine
from .initiative_spawner import InitiativeSpawner
from .autonomous_builder import AutonomousBuilder
from .validation_engine import ValidationEngine
from .policy_learner import PolicyLearner
from .priority_arbitrator import PriorityArbitrator
from .idle_work_generator import IdleWorkGenerator

class AlwaysOnCEO:
    """204: always-on executive cycle that prevents autonomous work starvation."""
    def __init__(self):
        self.continuity=GoalContinuityEngine(); self.spawner=InitiativeSpawner()
        self.builder=AutonomousBuilder(); self.validation=ValidationEngine()
        self.policy=PolicyLearner(); self.priority=PriorityArbitrator(); self.idle=IdleWorkGenerator()
    def tick(self,p):
        active_goals=self.continuity.reconcile(p.get("goals",[]),p.get("results",[]))
        spawned=self.spawner.spawn(active_goals,p.get("active_tasks",[]))
        ranked=self.priority.rank(list(p.get("active_tasks",[]))+spawned)
        idle=self.idle.generate(len(ranked),p.get("capacity",5))
        return {"success":True,"status":"phase204_always_on_ceo_tick_completed",
        "timestamp":datetime.now(timezone.utc).isoformat(),"active_goals":active_goals,
        "spawned_initiatives":spawned,"ranked_work":ranked,"idle_work":idle,
        "builder_next":self.builder.next(p.get("build_state",{})),
        "validation":self.validation.evaluate(p.get("evidence",{})),
        "learned_policies":self.policy.learn(p.get("behaviors",[])),
        "autonomy_mode":"high","always_on_ceo":True,"work_starvation_prevention":True,
        "external_action_taken":False,"financial_action_taken":False,"irreversible_action_taken":False}
