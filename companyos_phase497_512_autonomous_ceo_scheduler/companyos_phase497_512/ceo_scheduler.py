from companyos_phase465_480 import CEOState
from companyos_phase481_496 import MissionQueue, PersistentScheduler
from .objective_store import ObjectiveStore
from .mission_generator import MissionGenerator
from .mission_deduper import MissionDeduper
from .mission_budget import MissionBudget
from .mission_reprioritizer import MissionReprioritizer
from .scheduler_heartbeat import SchedulerHeartbeat
from .scheduler_state import SchedulerState
from .event_store import EventStore
from .stalled_work_detector import StalledWorkDetector

class AutonomousCEOScheduler:
    """510: generate, prioritize, execute, and persist CEO missions."""

    def __init__(self, root):
        self.root = root
        self.ceo_state = CEOState(root)
        self.objectives = ObjectiveStore(root)
        self.queue = MissionQueue(root)
        self.generator = MissionGenerator()
        self.deduper = MissionDeduper()
        self.budget = MissionBudget()
        self.reprioritizer = MissionReprioritizer()
        self.runner = PersistentScheduler(root)
        self.scheduler_state = SchedulerState(root)
        self.events = EventStore(root)

    def tick(self, context=None):
        context = dict(context or {})
        state = self.ceo_state.load()
        limits = self.budget.limits()

        generated = self.generator.generate(state, context)
        existing = self.queue.load()
        combined = self.deduper.unique(existing + generated)
        combined = self.reprioritizer.apply(combined)[:limits["max_queue_size"]]
        self.queue.save(combined)

        result = self.runner.run_once(max_missions=limits["max_execute_per_tick"])

        sched = self.scheduler_state.load()
        sched["ticks"] = int(sched.get("ticks",0)) + 1
        sched["last_status"] = result.get("status")
        sched["last_executed"] = result.get("executed_count",0)
        self.scheduler_state.save(sched)

        stalled = StalledWorkDetector().detect(self.queue.load())
        heartbeat = SchedulerHeartbeat().beat(
            queue_size=len(self.queue.load()),
            executed=result.get("executed_count",0),
        )

        self.events.append("scheduler_tick", {
            "generated": len(generated),
            "executed": result.get("executed_count",0),
            "remaining": result.get("remaining_count",0),
        })

        return {
            "success": True,
            "status": "autonomous_ceo_scheduler_tick_complete",
            "objectives": self.objectives.load(),
            "generated_missions": generated,
            "scheduler_result": result,
            "stalled_missions": stalled,
            "heartbeat": heartbeat,
            "scheduler_state": sched,
        }
