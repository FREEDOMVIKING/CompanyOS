import uuid
from .opportunity_engine import OpportunityEngine
from .experiment_engine import ExperimentEngine
from .portfolio_engine import PortfolioEngine
from .resource_allocator import ResourceAllocator
from .learning_engine import PortfolioLearningEngine
from .guardrails import VentureGuardrails

class AutonomousVentureFactory:
    def cycle(self, candidates, existing_ventures=None, actions=None, budget=10000, worker_slots=10):
        ranked=OpportunityEngine().rank(candidates)
        top=ranked[0] if ranked else None
        spawned=None
        if top and top["opportunity_score"]>=.55:
            spawned={
                "venture_id":"venture_"+uuid.uuid4().hex[:10],
                "name":top.get("name","new_venture"),
                "score":top["opportunity_score"],
                "growth":top.get("growth",.25),
                "reliability":top.get("reliability",.75),
                "stage":"validate",
                "experiments":ExperimentEngine().plan(top)
            }
        ventures=list(existing_ventures or [])
        if spawned: ventures.append(spawned)
        decisions=PortfolioEngine().decide(ventures)
        allocations=ResourceAllocator().allocate(decisions,budget,worker_slots)
        routing=VentureGuardrails().route(actions)
        lessons=PortfolioLearningEngine().learn(decisions)
        return {
            "success":True,
            "status":"autonomous_venture_factory_cycle_complete",
            "ranked_opportunities":ranked,
            "spawned_venture":spawned,
            "portfolio_decisions":decisions,
            "resource_allocations":allocations,
            "organizational_learning":lessons,
            **routing
        }
