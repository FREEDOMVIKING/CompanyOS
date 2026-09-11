from .event_bus import EventBus
from .durable_queue import DurableJobQueue
from .scheduler import AutonomousScheduler
from .daemon_state import DaemonState
from .supervisor import SelfHealingSupervisor
from .restart_recovery import RestartRecovery
from .trigger_router import TriggerRouter
from .runtime_audit import RuntimeAudit

class CEOAutonomousLoop:
    def __init__(self, root):
        self.root=root
        self.queue=DurableJobQueue(root)
        self.state=DaemonState(root)
        self.audit=RuntimeAudit(root)

    def run_tick(self, tick, scheduled_tasks=None, incoming_events=None, workers=None):
        scheduled=AutonomousScheduler().due(scheduled_tasks or [], tick)
        enqueued=[]
        for t in scheduled:
            enqueued.append(self.queue.enqueue(t.get("kind","scheduled_task"), t.get("payload",{}), t.get("priority",5)))

        routed=[]
        for e in incoming_events or []:
            event=EventBus().publish(e.get("kind"), e.get("payload",{}))
            route=TriggerRouter().route(event)
            routed.append(route)
            enqueued.append(self.queue.enqueue(
                kind="event_task",
                payload={"event":event,"department":route["department"]},
                priority=e.get("priority",7)
            ))

        next_job=self.queue.next_job()
        if next_job:
            self.queue.update(next_job["job_id"], status="running", attempts=int(next_job.get("attempts",0))+1)

        previous=self.state.load()
        recovery=RestartRecovery().plan(previous, self.queue.load())
        supervision=SelfHealingSupervisor().evaluate(workers or [])

        result={
            "success":True,
            "status":"autonomous_daemon_event_runtime_tick_complete",
            "tick":int(tick),
            "scheduled_due":scheduled,
            "routed_events":routed,
            "enqueued":enqueued,
            "next_job":next_job,
            "supervision":supervision,
            "recovery":recovery,
            "queue_depth":len([x for x in self.queue.load() if x.get("status") in ("queued","retry","running")])
        }
        self.state.save(result)
        self.audit.append("daemon_tick", result)
        return result
