from .priority_engine import PriorityEngine
from .resource_allocator import ResourceAllocator
from .venture_executor import VentureExecutor
from .venture_health import VentureHealth
from .portfolio_snapshot import PortfolioSnapshot

class ExecutionManager:
    """446: coordinate multiple ventures and pick what runs next."""

    def manage(self, ventures, max_active=2):
        enriched = []
        priority = PriorityEngine()
        health = VentureHealth()

        for venture in ventures:
            item = dict(venture)
            item["priority_score"] = priority.score(item)
            item["priority"] = item["priority_score"]
            item["health"] = health.evaluate(item)
            item["next_action"] = VentureExecutor().next_action(item)
            enriched.append(item)

        allocation = ResourceAllocator().allocate(enriched, max_active=max_active)

        return {
            "success":True,
            "status":"venture_execution_plan_ready",
            "allocation":allocation,
            "portfolio":PortfolioSnapshot().build(enriched),
            "ventures":enriched,
        }
