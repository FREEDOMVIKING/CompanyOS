from datetime import datetime,timezone
from .objective_tree import ObjectiveTree
from .initiative_factory import InitiativeFactory
from .agent_team_builder import AgentTeamBuilder
from .execution_supervisor import ExecutionSupervisor
from .evidence_learner import EvidenceLearner
from .venture_lifecycle import VentureLifecycle
from .capacity_manager import CapacityManager

class CompanyDaemon:
    """172: persistent heartbeat cycle coordinating self-directed company work."""
    def __init__(self):
        self.objectives=ObjectiveTree();self.initiatives=InitiativeFactory();self.teams=AgentTeamBuilder()
        self.supervisor=ExecutionSupervisor();self.learning=EvidenceLearner();self.lifecycle=VentureLifecycle();self.capacity=CapacityManager()
    def tick(self,p):
        initiatives=self.initiatives.create(p.get("goals",[]),p.get("gaps",[]))
        return {"success":True,"status":"phase172_company_daemon_tick_completed",
        "timestamp":datetime.now(timezone.utc).isoformat(),
        "objective_tree":self.objectives.build(p.get("primary_objective","grow_company"),p.get("objective_depth",1)),
        "initiatives":initiatives,
        "teams":[self.teams.assemble({**x,"capabilities":p.get("default_capabilities",[])},p.get("agents",[])) for x in initiatives],
        "execution":self.supervisor.supervise(p.get("jobs",[])),
        "beliefs":self.learning.update(p.get("beliefs",[]),p.get("evidence",[])),
        "venture_actions":[self.lifecycle.decide(v) for v in p.get("ventures",[])],
        "capacity":self.capacity.allocate(p.get("total_capacity",100)),
        "autonomy_mode":"high","persistent_heartbeat":True,
        "external_action_taken":False,"financial_action_taken":False,"irreversible_action_taken":False}
