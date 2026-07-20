from datetime import datetime,timezone
from .intent_engine import IntentEngine
from .hypothesis_factory import HypothesisFactory
from .experiment_loop import ExperimentLoop
from .autonomous_architect import AutonomousArchitect
from .service_supervisor import ServiceSupervisor
from .memory_consolidator import MemoryConsolidator
from .growth_flywheel import GrowthFlywheel

class CompanyKernel:
    """196: persistent mission -> intent -> hypothesis -> experiment -> learning kernel."""
    def __init__(self):
        self.intent=IntentEngine();self.hypotheses=HypothesisFactory();self.experiments=ExperimentLoop()
        self.architect=AutonomousArchitect();self.services=ServiceSupervisor()
        self.memory=MemoryConsolidator();self.growth=GrowthFlywheel()
    def tick(self,p):
        intents=self.intent.generate(p.get("mission"),p.get("state",{}))
        hypotheses=self.hypotheses.create(intents)
        return {"success":True,"status":"phase196_company_kernel_tick_completed",
        "timestamp":datetime.now(timezone.utc).isoformat(),"intents":intents,"hypotheses":hypotheses,
        "experiment_states":[self.experiments.next(x) for x in p.get("experiments",[])],
        "architecture":self.architect.evaluate(p.get("architecture_proposal",{})),
        "service_actions":self.services.inspect(p.get("services",[])),
        "memory_lessons":self.memory.consolidate(p.get("observations",[])),
        "growth_flywheel":self.growth.evaluate(p.get("growth_state",{})),
        "autonomy_mode":"high","persistent_kernel":True,
        "external_action_taken":False,"financial_action_taken":False,"irreversible_action_taken":False}
